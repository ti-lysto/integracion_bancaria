"""
MÓDULO DE SEGURIDAD R4 CONECTA
==============================

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

CREADO POR: Alicson Rubio
FECHA: Noviembre 2025
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from core.config import get_r4_config

logger = logging.getLogger(__name__)

class R4Security:
    """
    CLASE PARA MANEJAR SEGURIDAD R4
    
    ¿Qué hace?
    - Valida firmas HMAC de notificaciones bancarias
    - Verifica que el comercio sea el correcto
    - Genera firmas para respuestas al banco
    """
    
    def __init__(self):
        pass # agregado para saber sonde se llama a security.py por si hay algun error al unificar security.py y auth.py
#         """
#         INICIALIZAR SEGURIDAD R4
        
#         ¿Qué hace?
#         - Obtiene la configuración de seguridad
#         - Prepara las claves para validación
#         """
#         self.config = get_r4_config()
#         self.merchant_id = self.config["merchant_id"]
#         self.secret_key = self.config["secret_key"]
    
#     def validate_hmac_signature(self, data: Dict[str, Any], signature: str) -> bool:
#         """
#         VALIDAR FIRMA HMAC DE UNA NOTIFICACIÓN
        
#         ¿Qué hace?
#         1. Convierte los datos a string JSON ordenado
#         2. Calcula la firma HMAC-SHA256 esperada
#         3. Compara con la firma recibida del banco
#         4. Retorna True si coinciden, False si no
        
#         Parámetros:
#         - data: Datos de la notificación del banco
#         - signature: Firma HMAC recibida en el header
        
#         Retorna:
#         - True si la firma es válida, False si no
#         """
#         try:
#             # Validar que data no esté vacío
#             if not data:
#                 logger.error("Datos vacíos para validación HMAC")
#                 return False
                
#             # Crear string para firmar (JSON ordenado)
#             data_string = self._create_signature_string(data)
            
#             # Calcular firma esperada
#             expected_signature = self._calculate_hmac(data_string)
            
#             # Comparar firmas de forma segura
#             is_valid = hmac.compare_digest(expected_signature, signature)
            
#             if is_valid:
#                 logger.info(f"Firma HMAC válida para referencia: {data.get('Referencia', 'N/A')}")
#             else:
#                 logger.warning(f"Firma HMAC inválida para referencia: {data.get('Referencia', 'N/A')}")
#                 logger.debug(f"Esperada: {expected_signature}")
#                 logger.debug(f"Recibida: {signature}")
            
#             return is_valid
            
    #     except Exception as e:
    #         logger.error(f"Error validando firma HMAC: {str(e)}")
    #         return False
    
    # def validate_merchant_id(self, notification_data: Dict[str, Any]) -> bool:
    #     """
    #     VALIDAR QUE LA NOTIFICACIÓN SEA PARA NUESTRO COMERCIO
        
    #     ¿Qué hace?
    #     - Verifica que el IdComercio en la notificación coincida con el nuestro
    #     - Previene procesar notificaciones de otros comercios
        
    #     Parámetros:
    #     - notification_data: Datos de la notificación
        
    #     Retorna:
    #     - True si es para nuestro comercio, False si no
    #     """
    #     try:
    #         if not notification_data:
    #             logger.error("Datos de notificación vacíos")
    #             return False
                
    #         received_merchant_id = notification_data.get("IdComercio", "")
            
    #         # Comparar IDs de comercio
#             is_valid = received_merchant_id == self.merchant_id
            
#             if is_valid:
#                 logger.info(f"Notificación válida para comercio: {self.merchant_id}")
#             else:
#                 logger.warning(f"Notificación para comercio incorrecto. Esperado: {self.merchant_id}, Recibido: {received_merchant_id}")
            
#             return is_valid
            
#         except Exception as e:
#             logger.error(f"Error validando merchant ID: {str(e)}")
#             return False
    
#     def generate_response_signature(self, response_data: Dict[str, Any]) -> str:
#         """
#         GENERAR FIRMA PARA RESPUESTA AL BANCO
        
#         ¿Qué hace?
#         - Crea una firma HMAC para nuestra respuesta
#         - El banco puede verificar que la respuesta viene de nosotros
        
#         Parámetros:
#         - response_data: Datos de la respuesta que enviaremos
        
#         Retorna:
#         - Firma HMAC-SHA256 de la respuesta
#         """
#         try:
#             # Validar datos de respuesta
#             if not response_data:
#                 logger.error("Datos de respuesta vacíos")
#                 return ""
                
#             # Crear string para firmar
#             data_string = self._create_signature_string(response_data)
            
#             # Calcular y retornar firma
#             signature = self._calculate_hmac(data_string)
            
#             logger.debug(f"Firma generada para respuesta: {signature}")
#             return signature
            
#         except Exception as e:
#             logger.error(f"Error generando firma de respuesta: {str(e)}")
#             return ""
    
#     def _create_signature_string(self, data: Dict[str, Any]) -> str:
#         """
#         CREAR STRING PARA FIRMAR SEGÚN ESPECIFICACIÓN R4
        
#         ¿Qué hace?
#         - Convierte el diccionario a JSON ordenado
#         - Elimina espacios extra
#         - Crea string consistente para firmar
        
#         Parámetros:
#         - data: Diccionario con los datos
        
#         Retorna:
#         - String listo para firmar
#         """
#         try:
#             # Convertir a JSON ordenado (sin espacios)
#             json_string = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            
#             logger.debug(f"String para firmar: {json_string[:100]}...")  # Solo primeros 100 chars en log
#             return json_string
#         except (TypeError, ValueError) as e:
#             logger.error(f"Error creando string para firma: {str(e)}")
#             raise
    
#     def _calculate_hmac(self, data_string: str) -> str:
#         """
#         CALCULAR FIRMA HMAC-SHA256
        
#         ¿Qué hace?
#         - Usa la clave secreta del banco
#         - Aplica algoritmo HMAC-SHA256
#         - Retorna firma en hexadecimal
        
#         Parámetros:
#         - data_string: String a firmar
        
#         Retorna:
#         - Firma HMAC en formato hexadecimal
#         """
#         # Convertir clave y datos a bytes
#         key_bytes = self.secret_key.encode('utf-8')
#         data_bytes = data_string.encode('utf-8')
        
#         # Calcular HMAC-SHA256
#         signature = hmac.new(key_bytes, data_bytes, hashlib.sha256).hexdigest()
        
#         return signature

# # Instancia global de seguridad
# r4_security = R4Security()

# def validate_r4_notification(notification_data: Dict[str, Any], auth_token: Optional[str] = None) -> Dict[str, Any]:
#     """
#     VALIDAR COMPLETAMENTE UNA NOTIFICACIÓN R4
    
#     Según especificación del banco:
#     1. Validar que sea para nuestro comercio (IdComercio)
#     2. Validar formato UUID del token Authorization
#     3. Validar referencia, banco y monto (validación de negocio)
    
#     Parámetros:
#     - notification_data: Datos de la notificación
#     - auth_token: Token UUID del header Authorization
    
#     Retorna:
#     - Diccionario con resultado de validación
#     """
#     try:
#         logger.info(f"Validando notificación R4 - Ref: {notification_data.get('Referencia', 'N/A')}")
        
#         # 1. Validar merchant ID
#         if not r4_security.validate_merchant_id(notification_data):
#             return {
#                 "valid": False,
#                 "error": "Notificación no es para este comercio",
#                 "code": "INVALID_MERCHANT"
#             }
        
#         # 2. Validar formato UUID del token (según especificación del banco)
#         if auth_token:
#             import uuid
#             try:
#                 uuid.UUID(auth_token)
#                 logger.info(f"Token UUID válido: {auth_token[:8]}...")
#             except ValueError:
#                 logger.error(f"Token no es UUID válido: {auth_token}")
#                 return {
#                     "valid": False,
#                     "error": "Token Authorization debe ser UUID válido",
#                     "code": "INVALID_TOKEN_FORMAT"
#                 }
        
#         # 3. Validación de negocio (referencia, banco, monto)
#         validation_result = _validate_business_rules(notification_data)
#         if not validation_result["valid"]:
#             return validation_result
        
#         # 4. Validación exitosa
#         logger.info(f"Notificación R4 válida - Ref: {notification_data.get('Referencia', 'N/A')}")
#         return {
#             "valid": True,
#             "message": "Notificación válida",
#             "code": "VALID"
#         }
        
#     except Exception as e:
#         logger.error(f"Error validando notificación R4: {str(e)}")
#         return {
#             "valid": False,
#             "error": f"Error de validación: {str(e)}",
#             "code": "VALIDATION_ERROR"
#         }

# def _validate_business_rules(notification_data: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     VALIDAR REGLAS DE NEGOCIO REQUERIDAS POR EL BANCO
    
#     Según documento: "El cliente debe validar dentro de su desarrollo los datos 
#     notificados, para ello es necesario que realice un proceso de verificación de 
#     referencia, banco y monto antes de abonar al cliente final."
    
#     """
#     try:
#         # Validar que la referencia no esté duplicada
#         referencia = notification_data.get('Referencia', '')
#         if not referencia or len(referencia) < 6:
#             return {
#                 "valid": False,
#                 "error": "Referencia inválida o muy corta",
#                 "code": "INVALID_REFERENCE"
#             }
        
#         # Validar código de banco
#         banco = notification_data.get('BancoEmisor', '')
#         if not banco or len(banco) != 3 or not banco.isdigit():
#             return {
#                 "valid": False,
#                 "error": "Código de banco inválido",
#                 "code": "INVALID_BANK_CODE"
#             }
        
#         # Validar monto
#         monto = notification_data.get('Monto', '')
#         try:
#             monto_float = float(monto)
#             if monto_float <= 0:
#                 return {
#                     "valid": False,
#                     "error": "Monto debe ser mayor a cero",
#                     "code": "INVALID_AMOUNT"
#                 }
#         except (ValueError, TypeError):
#             return {
#                 "valid": False,
#                 "error": "Formato de monto inválido",
#                 "code": "INVALID_AMOUNT_FORMAT"
#             }
        
#         # Validar código de red (debe ser "00" para aprobado)
#         codigo_red = notification_data.get('CodigoRed', '')
#         if codigo_red != "00":
#             return {
#                 "valid": False,
#                 "error": f"Transacción no aprobada - Código: {codigo_red}",
#                 "code": "TRANSACTION_NOT_APPROVED"
#             }
        
#         return {"valid": True}
        
#     except Exception as e:
#         logger.error(f"Error en validación de negocio: {str(e)}")
#         return {
#             "valid": False,
#             "error": f"Error en validación de negocio: {str(e)}",
#             "code": "BUSINESS_VALIDATION_ERROR"
#         }