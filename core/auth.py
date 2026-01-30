"""
AUTENTICACIÓN Y SEGURIDAD R4
============================

¿QUÉ ES ESTE ARCHIVO?
- Implementa la autenticación HMAC-SHA256 según especificación R4
- Valida que las notificaciones realmente vengan del banco
- Previene ataques de falsificación y manipulación de datos

¿POR QUÉ ES IMPORTANTE?
- Garantiza que solo el banco pueda enviar notificaciones válidas
- Protege contra ataques maliciosos
- Cumple con los estándares de seguridad bancaria

¿CÓMO FUNCIONA?
- El banco firma cada notificación con HMAC-SHA256
- Nosotros verificamos la firma usando la misma clave secreta
- Si la firma no coincide, rechazamos la notificación

Creado por: Alicson Rubio
Fecha: Noviembre 2025
"""

import hmac
import hashlib
import logging
import uuid
from fastapi import HTTPException, Header, Request, Depends
from typing import Optional, Dict, Any, List
from core.config import get_r4_config

logger = logging.getLogger(__name__)

# obtener clave secreta desde configuración
config = get_r4_config()
SECRET_KEY = config.get("merchant_id") 
# =====================================================
# CONFIGURACIÓN DE HMAC POR ENDPOINT
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
        "params": ["id"],
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
        if (token == get_r4_config().get("uuid")):
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