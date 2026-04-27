
import hmac
import hashlib
import logging
import uuid
import base64
import os
import json
from fastapi import HTTPException, Header, Request, Depends
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Optional, Dict, Any, List
from core.config import get_r4_config
from core.config import get_bancaribe_config
from core.config import get_encryption_config

logger = logging.getLogger(__name__)

# obtener clave secreta desde configuración
config = get_r4_config()
SECRET_KEY = config.get("merchant_id") 
# =====================================================
# CONFIGURACIÓN para bancos que usan HMAC (R4) - parámetros y formato de string a firmar
# =====================================================

HMAC_CONFIG = {
    "MBbcv": {
        "params": ["Fechavalor", "Moneda"],
        "separator": "",  # fechavalor + moneda (sin separador)
        "requires_uuid": False
    },
    "R4pagos": {
        "params": ["monto", "fecha"],  # fecha en MM/DD/AAAA
        "separator": "",  # monto + fecha
        "requires_uuid": False
    },
    "MBvuelto": {
        "params": ["TelefonoDestino", "Monto", "Banco", "Cedula"],
        "separator": "",  # TelefonoDestino + Monto + Banco + Cedula
        "requires_uuid": False
    },
    "GenerarOtp": {
        "params": ["Banco", "Monto", "Telefono", "Cedula"],
        "separator": "",  # Banco + Monto + Telefono + Cedula
        "requires_uuid": False
    },
    "DebitoInmediato": {
        "params": ["Banco", "Cedula", "Telefono", "Monto", "OTP"],
        "separator": "",  # Banco + Cedula + Telefono + Monto + OTP
        "requires_uuid": False
    },
    "CreditoInmediato": {
        "params": ["Banco", "Cedula", "Telefono", "Monto"],
        "separator": "",  # Banco + Cedula + Telefono + Monto
        "requires_uuid": False
    },
    "DomiciliacionCNTA": {
        "params": ["cuenta"],
        "separator": "",  # solo cuenta
        "requires_uuid": False
    },
    "DomiciliacionCELE": {
        "params": ["telefono"],
        "separator": "",  # solo telefono
        "requires_uuid": False
    },
    "ConsultarOperaciones": {
        "params": ["Id"],
        "separator": "",  # solo id
        "requires_uuid": False
    },
    "CICuentas": {
        "params": ["Cedula", "Cuenta", "Monto"],
        "separator": "",  # Cedula + Cuenta + Monto
        "requires_uuid": False
    },
    "MBc2p": {
        "params": ["TelefonoDestino", "Monto", "Banco", "Cedula"],
        "separator": "",  # TelefonoDestino + Monto + Banco + Cedula
        "requires_uuid": False
    },
    "MBanulacionC2P": {
        "params": ["Banco"],
        "separator": "",  # solo Banco
        "requires_uuid": False
    },
    "VerificoPago": {
        "params": ["Referencia"],
        "separator": "",
        "requires_uuid": False
    },
    "R4consulta": {
        "params": [],  # No usa HMAC, solo UUID
        "requires_uuid": True
    },
    "R4notifica": {
        "params": [],  # No usa HMAC, solo UUID
        "requires_uuid": True
    }
}

TOKEN_CONGIG_BANCARIBE = {    
    "params": ["KEY","SECRET"],
    "separator": ":",  # KEY:SECRET
}

def calcular_hmac_r4(data_string: str, secret_key: str) -> str:
    """Calcular HMAC-SHA256 según especificación R4"""
    try:
        
        return hmac.new(
            secret_key.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    except Exception as e:
        logger.error(f"Error calculando HMAC: {str(e)}")
        raise

def verificar_hmac_r4(data_string: str, signature_received: str, secret_key: str) -> bool:
    """Verificar HMAC de forma segura (timing-attack safe)"""
    try:
        expected_signature = calcular_hmac_r4(data_string, secret_key)
        #print (f"esperado: {expected_signature}, recibido: {signature_received}")
        return hmac.compare_digest(expected_signature, signature_received)
    except Exception as e:
        logger.error(f"Error verificando HMAC: {str(e)}")
        return False

def validar_uuid(token: str) -> bool:
    """Validar que el token sea un UUID válido (para R4consulta y R4notifica)"""
    try:
        #if (uuid.UUID(token)) or (token == get_r4_config().get("uuid")):   
        if (token == get_r4_config().get("R4_UUID")):
            return True
        else:
            return False    
    except ValueError:
        return False


class R4Authentication:
    """Clase ligera que expone métodos para generar firmas (HMAC) usadas
    por los clientes cuando necesitan enviar solicitudes firmadas al banco.

    Usamos las funciones existentes `calcular_hmac_r4` y la configuración
    central (`get_r4_config()`) para obtener la clave.
    """

    def __init__(self):
        self.config = get_r4_config()

    def generate_response_signature(self, response_data: Dict[str, Any]) -> str:
        """Genera una firma HMAC-SHA256 para `response_data`.

        Comportamiento simple y compatible con el uso actual en `r4_services`:
        - Si response_data contiene la clave 'data' y es string, la firmamos
        directamente.
        - En cualquier otro caso, serializamos a JSON ordenado y firmamos.
        """
        try:
            # Preferir campo 'data' si existe (uso actual en r4_services)
            if isinstance(response_data, dict) and "data" in response_data:
                data_string = str(response_data["data"])
            else:
                # Serializar de forma determinística
                import json
                data_string = json.dumps(response_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

            secret = self.config.get("merchant_id")  # Usar merchant_id como clave secreta
            if not secret:
                logger.error("Clave secreta no configurada para generar firma")
                return ""

            return calcular_hmac_r4(data_string, secret)
        except Exception as e:
            logger.error(f"Error generando signature: {e}")
            return ""


# Instancia pública que otros módulos pueden importar
r4_authentication = R4Authentication()
    
async def ip_whitelist_middleware(request: Request):
    """" Middleware para validar IPs permitidas en R4 endpoints."""
    client_ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.client.host if request.client else "unknown"))
    if client_ip not in get_r4_config().get("allowed_ips", []):
        logger.warning(f"Intento de acceso desde IP no autorizada: {client_ip}")
        raise HTTPException(status_code=401, detail=f"IP {client_ip} no autorizada. Solo se permiten conexiones desde los servidores del banco.")
    return True
 
# =====================================================
# FUNCIÓN GENÉRICA PARA VALIDACIÓN HMAC
# =====================================================

async def validar_hmac_generico(
    endpoint: str,
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None =  None
) -> bool:
    """
    Función genérica para validar HMAC según endpoint
    """
    if not authorization:
        logger.error(f"Header Authorization faltante para {endpoint}")
        raise HTTPException(status_code=401, detail="Authorization header requerido")

    config = get_r4_config()
    hmac_config = HMAC_CONFIG.get(endpoint)
    
    if not hmac_config:
        logger.error(f"Configuración HMAC no encontrada para endpoint: {endpoint}")
        raise HTTPException(status_code=500, detail="Error de configuración de seguridad")
    
    # Validación para endpoints que solo requieren UUID
    if hmac_config["requires_uuid"]:
        if not validar_uuid(authorization):
            logger.error(f"Token UUID inválido para {endpoint}: {authorization}")
            raise HTTPException(status_code=401, detail="Token Authorization debe ser UUID válido")
        return True
    
    # Validación HMAC para endpoints que requieren firma criptográfica
    try:
        # Construir string según parámetros configurados
        data_parts = []
        assert payload is not None, "El payload no debe ser None"
        for param in hmac_config["params"]:
            value = payload.get(param)
            if value is None:
                logger.error(f"Parámetro faltante para HMAC {endpoint}: {param}")
                raise HTTPException(status_code=400, detail=f"Parámetro {param} requerido para autenticación")
            data_parts.append(str(value))
        
        data_string = hmac_config["separator"].join(data_parts)
        
        # Verificar HMAC
        if not verificar_hmac_r4(data_string, authorization, config["merchant_id"]):
            logger.error(f"HMAC inválido para {endpoint}")
            logger.error(f"Data string: {data_string}")
            logger.error(f"Firma recibida: {authorization}")
            raise HTTPException(status_code=401, detail="Firma HMAC inválida")
        
        logger.info(f"HMAC válido para {endpoint}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando HMAC para {endpoint}: {str(e)}")
        raise HTTPException(status_code=401, detail="Error de autenticación")

# CONSULTA BCV
async def verify_hmac_bcv(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
): 
    print(authorization, payload)
    return await validar_hmac_generico("MBbcv", authorization, payload)

# GESTIÓN DE PAGOS
async def verify_hmac_pagos(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("R4pagos", authorization, payload)

# VUELTO
async def verify_hmac_vuelto(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("MBvuelto", authorization, payload)

# GENERAR OTP
async def verify_hmac_generar_otp(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    
    return await validar_hmac_generico("GenerarOtp", authorization, payload)

# DÉBITO INMEDIATO
async def verify_hmac_debito_inmediato(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("DebitoInmediato", authorization, payload)

# CRÉDITO INMEDIATO
async def verify_hmac_credito_inmediato(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("CreditoInmediato", authorization, payload)

# DOMICILIACIÓN POR CUENTA
async def verify_hmac_domiciliacion_cnta(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("DomiciliacionCNTA", authorization, payload)

# DOMICILIACIÓN POR TELÉFONO
async def verify_hmac_domiciliacion_cele(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("DomiciliacionCELE", authorization, payload)

# CONSULTAR OPERACIONES
async def verify_hmac_consultar_operaciones(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("ConsultarOperaciones", authorization, payload)

# CRÉDITO INMEDIATO CUENTAS
async def verify_hmac_ci_cuentas(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("CICuentas", authorization, payload)

# COBRO C2P
async def verify_hmac_c2p(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("MBc2p", authorization, payload)

# ANULACIÓN C2P
async def verify_hmac_anulacion_c2p(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("MBanulacionC2P", authorization, payload)

# VERIFICO PAGO
async def verify_hmac_verifico_pago(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("VerificoPago", authorization, payload)

# CONSULTA
async def verify_hmac_consulta(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("R4consulta", authorization, payload)

# NOTIFICA
async def verify_hmac_notifica(
    authorization: Optional[str] = Header(None),
    payload: Dict[str, Any] | None = None
):
    return await validar_hmac_generico("R4notifica", authorization, payload)
# =====================================================
# VALIDACIÓN PARA R4CONSULTA Y R4NOTIFICA (SOLO UUID)
# =====================================================

async def require_headers(
    authorization: Optional[str] = Header(None),
    commerce: Optional[str] = Header(None)
):
    config = get_r4_config()
    uuid_env = config.get("uuid")
    if authorization != uuid_env:
        raise HTTPException(status_code=401, detail="UUID inválido")
    
    """
    Validación para R4consulta y R4notifica según especificación:
    - Authorization: UUID válido
    - Commerce: ID del comercio
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Header Authorization requerido")
    
    if not commerce:
        raise HTTPException(status_code=401, detail="Header Commerce requerido")
    
    # Validar UUID
    if not validar_uuid(authorization):
        logger.error(f"Token UUID inválido: {authorization}")
        raise HTTPException(status_code=401, detail="Token Authorization debe ser UUID válido")
    
    # Validar commerce ID (opcional: verificar contra configuración)
    config = get_r4_config()
    if commerce != config["merchant_id"]:
        logger.warning(f"Commerce ID no coincide: recibido {commerce}, esperado {config['merchant_id']}")
        # No rechazamos por esto, solo log warning según especificación
    
    logger.info(f"Headers válidos para consulta/notifica - Commerce: {commerce}")
    return True

# Funciones de autenticación para cada endpoint
# async def verify_hmac_bcv(authorization: Optional[str] = Header(None), request: Request = None):
#     """Verificar HMAC para consulta BCV"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     try:
#         # Obtener el cuerpo de la solicitud
#         body = await request.body()
#         data_string = body.decode('utf-8')
#         if not verify_hmac(data_string, authorization):
#             raise HTTPException(status_code=401, detail="Firma HMAC no válida")
#         return True
#     except Exception as e:
#         logger.error(f"Error validando HMAC: {str(e)}")
#         raise HTTPException(status_code=401, detail="Error de autenticación")
    
# async def verify_hmac_pagos(authorization: Optional[str] = Header(None), request: Request = None):
#     """Verificar HMAC para gestión de pagos"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_vuelto(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para vuelto"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_generar_otp(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para generar OTP"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_debito_inmediato(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para débito inmediato"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_credito_inmediato(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para crédito inmediato"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_domiciliacion_cnta(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para domiciliación por cuenta"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_domiciliacion_cele(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para domiciliación por teléfono"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_consultar_operaciones(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para consultar operaciones"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_ci_cuentas(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para crédito inmediato con cuentas"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_c2p(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para cobro C2P"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def verify_hmac_anulacion_c2p(authorization: Optional[str] = Header(None)):
#     """Verificar HMAC para anulación C2P"""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header requerido")
#     return True

# async def require_headers(
#     authorization: Optional[str] = Header(None),
#     commerce: Optional[str] = Header(None)
# ):
#     """Verificar headers requeridos para R4consulta y R4notifica"""
#     if not authorization or not commerce:
#         raise HTTPException(status_code=401, detail="Headers Authorization y Commerce requeridos")
#     return True

# =====================================================
# Autenticación específica para Bancaribe 
# =====================================================
from services.bancos.banco_bancaribe import BancoBancaribeService

class BancaribeAuth:
    """Clase de autenticación específica para endpoints de Bancaribe.
    Aquí podemos implementar validaciones adicionales específicas para este banco,
    como verificar tokens, claves o formatos que ellos requieran.
    """

    def __init__(self):
        self.service = BancoBancaribeService()

    async def verify_bancaribe_token(self, token: str) -> bool:
        """Ejemplo de método para verificar un token específico de Bancaribe.
        En este caso, simplemente lo comparamos con un valor esperado desde configuración,
        pero aquí podríamos hacer llamadas a servicios externos, bases de datos, etc.
        """
        expected_token = self.service.calcular_base64_bancaribe()  # O el endpoint específico que corresponda
        if token == expected_token:
            return True
        else:
            logger.warning(f"Token de Bancaribe inválido: {token}")
            raise HTTPException(status_code=401, detail="Token de autenticación de Bancaribe inválido")

class encryption_bd:
    """Clase de autenticación específica para encriptación de datos en la base de datos.
    Aquí podemos implementar métodos para encriptar y desencriptar datos sensibles
    usando la clave definida en configuración.
    """

    def __init__(self):
        try:
            self.config = get_encryption_config()
            self.encrypt_method = self.config.get("algorithm", "")
            self.enc_key = self.config.get("enc_key", "").encode('utf-8')
            self.iterations = self.config.get("iterations", 0)
            self.backend = default_backend()

            if not self.enc_key:
                logger.warning("Clave de encriptación no configurada")

        except Exception as e:
            logger.error(f"Error inicializando encriptación: {str(e)}")
            raise
        
    def _pad(self, data: bytes, block_size: int = 16) -> bytes:
        """
        Aplicar padding PKCS7 (compatible con OpenSSL en PHP)
        
        Args:
            data: Datos a padding
            block_size: Tamaño del bloque (16 para AES)
            
        Returns:
            Datos con padding aplicado
        """
        padding_length = block_size - (len(data) % block_size)
        return data + bytes([padding_length] * padding_length)
    
    def _unpad(self, data: bytes) -> bytes:
        """
        Remover padding PKCS7
        
        Args:
            data: Datos con padding
            
        Returns:
            Datos originales sin padding
        """
        if not data:
            raise ValueError("No hay datos para unpadding")
        
        padding_length = data[-1]
        
        # Validar que el padding sea correcto
        if padding_length > 16:
            raise ValueError(f"Padding inválido: {padding_length} > 16")
        
        # Verificar que todos los bytes de padding sean iguales
        for i in range(1, padding_length + 1):
            if data[-i] != padding_length:
                raise ValueError("Padding corrupto")
        
        return data[:-padding_length]
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derivar clave usando PBKDF2 (compatible con PHP)
        
        Args:
            salt: Sal aleatoria (256 bytes)
            
        Returns:
            Clave derivada de 32 bytes (256 bits)
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,  # 32 bytes = 256 bits para AES-256
            salt=salt,
            iterations=self.iterations,
            backend=self.backend
        )
        return kdf.derive(self.enc_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encriptar un texto plano (COMPATIBLE CON PHP)
        
        Args:
            plaintext: Texto plano a encriptar
            
        Returns:
            String encriptado en formato base64(JSON)
            
        Ejemplo:
            encrypted = enc.encrypt("nombre=Juan&email=juan@example.com")
        """
        try:
            if not self.enc_key:
                raise ValueError("Clave de encriptación no configurada en .env")
            
            # Generar IV (16 bytes para AES-CBC)
            iv = os.urandom(16)
            
            # Generar salt (256 bytes como en PHP)
            salt = os.urandom(256)
            
            # Derivar clave
            key = self._derive_key(salt)
            
            # Aplicar padding a los datos
            padded_data = self._pad(plaintext.encode('utf-8'))
            
            # Crear cipher y encriptar
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            
            # Codificar en base64
            ciphertext_b64 = base64.b64encode(encrypted).decode('utf-8')
            
            # Construir el output (mismo formato que PHP)
            output = {
                'ciphertext': ciphertext_b64,
                'iv': iv.hex(),
                'salt': salt.hex(),
                'iterations': self.iterations
            }
            
            # Retornar base64(JSON)
            result = base64.b64encode(json.dumps(output).encode('utf-8')).decode('utf-8')
            
            logger.debug(f"✅ Datos encriptados exitosamente. Longitud: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error encriptando datos: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error de encriptación: {str(e)}")
    
    def decrypt(self, encrypted_string: str) -> Dict[str, Any]:
        """
        Desencriptar y convertir a diccionario (COMPATIBLE CON PHP)
        
        Args:
            encrypted_string: String encriptado en formato base64(JSON)
            
        Returns:
            Diccionario con los datos desencriptados
            
        Ejemplo:
            data = enc.decrypt(encrypted_string)
            print(data['nombre'])  # 'Juan'
        """
        try:
            if not self.enc_key:
                raise ValueError("Clave de encriptación no configurada")
            
            # Decodificar el string base64 para obtener el JSON
            json_str = base64.b64decode(encrypted_string).decode('utf-8')
            data = json.loads(json_str)
            
            # Extraer componentes
            salt = bytes.fromhex(data['salt'])
            iv = bytes.fromhex(data['iv'])
            ciphertext = base64.b64decode(data['ciphertext'])
            iterations = int(data.get('iterations', 999))
            
            # Derivar la misma clave
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA512(),
                length=32,
                salt=salt,
                iterations=iterations,
                backend=self.backend
            )
            key = kdf.derive(self.enc_key)
            
            # Descifrar
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remover padding
            decrypted = self._unpad(decrypted_padded)
            
            # Decodificar a string
            decrypted_str = decrypted.decode('utf-8')
            
            # Convertir a diccionario (como parse_str en PHP)
            result = self._parse_str(decrypted_str)
            
            logger.debug(f"✅ Datos desencriptados exitosamente. Campos: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error desencriptando datos: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error de desencriptación: {str(e)}")
    
    def decrypt_free(self, encrypted_string: str) -> str:
        """
        Desencriptar y retornar string puro (COMPATIBLE CON PHP)
        
        Args:
            encrypted_string: String encriptado en formato base64(JSON)
            
        Returns:
            String plano desencriptado
            
        Ejemplo:
            text = enc.decrypt_free(encrypted_string)
            # "nombre=Juan&email=juan@example.com&edad=30"
        """
        try:
            if not self.enc_key:
                raise ValueError("Clave de encriptación no configurada")
            
            # Decodificar el string base64 para obtener el JSON
            json_str = base64.b64decode(encrypted_string).decode('utf-8')
            data = json.loads(json_str)
            
            # Extraer componentes
            salt = bytes.fromhex(data['salt'])
            iv = bytes.fromhex(data['iv'])
            ciphertext = base64.b64decode(data['ciphertext'])
            iterations = int(data.get('iterations', 999))
            
            # Derivar la misma clave
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA512(),
                length=32,
                salt=salt,
                iterations=iterations,
                backend=self.backend
            )
            key = kdf.derive(self.enc_key)
            
            # Descifrar
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remover padding
            decrypted = self._unpad(decrypted_padded)
            
            # Reemplazar + por %2B (compatible con PHP)
            result = decrypted.decode('utf-8').replace('+', '%2B')
            
            logger.debug(f"✅ Datos desencriptados free exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error desencriptando datos (free): {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error de desencriptación: {str(e)}")
    
    def _parse_str(self, query_string: str) -> Dict[str, Any]:
        """
        Simular parse_str de PHP
        
        Args:
            query_string: String en formato "clave1=valor1&clave2=valor2"
            
        Returns:
            Diccionario con los pares clave=valor
        """
        result = {}
        
        if not query_string:
            return result
        
        # Reemplazar + por %2B (compatible con PHP)
        query_string = query_string.replace('+', '%2B')
        
        # Decodificar percent-encoding
        from urllib.parse import unquote
        query_string = unquote(query_string)
        
        # Parsear cada par
        for pair in query_string.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                result[key] = value
            elif pair:  # Clave sin valor
                result[pair] = ''
        
        return result
    
    def encrypt_dict(self, data_dict: Dict[str, Any]) -> str:
        """
        Encriptar un diccionario directamente
        
        Args:
            data_dict: Diccionario a encriptar
            
        Returns:
            String encriptado
            
        Ejemplo:
            data = {"nombre": "Juan", "email": "juan@email.com"}
            encrypted = enc.encrypt_dict(data)
        """
        # Convertir diccionario a string formato query
        query_string = '&'.join([f"{k}={v}" for k, v in data_dict.items()])
        return self.encrypt(query_string)
    
    def decrypt_to_dict(self, encrypted_string: str) -> Dict[str, Any]:
        """
        Desencriptar directamente a diccionario (alias de decrypt)
        """
        return self.decrypt(encrypted_string)


# Instancia global para usar en toda la aplicación
encryption_service = encryption_bd()


