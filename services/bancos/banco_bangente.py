"""SERVICIO PARA BANCO BANGENTE - EXPLICACIÓN DETALLADA
=====================================================

¿QUÉ ES ESTE ARCHIVO?
---------------------
Este archivo es el ESPECIALISTA que sabe cómo hablar específicamente
con el Banco Bangente (código oficial: 0146).

Es como tener un TRADUCTOR que entiende el idioma de Bangente y
sabe exactamente cómo procesar sus peticiones.

¿CUÁNDO SE USA?
--------------
Cuando alguien hace una petición a:
- /api/0146/MBbcv (por código)
- /api/bangente/MBbcv (por alias)

El sistema automáticamente usa ESTE archivo para procesarla.

¿QUÉ PUEDE HACER?
----------------
1. consultar_tasa(): Responde consultas sobre el precio del dólar
2. consulta_cliente(): Verifica si un cliente existe en el sistema
3. procesar_notificacion(): Recibe y procesa notificaciones de pagos

FLUJO DE INFORMACIÓN:
--------------------
PETICIÓN → ESTE ARCHIVO → PROCESA → RESPUESTA

EJEMPLO DE USO:
Bangente pregunta: ¿Cuál es la tasa del dólar hoy?
Este archivo responde: La tasa es 0.0 bolívares por dólar

Creado por: Alicson Rubio
"""
from typing import Dict, Any
import logging
from services.bancos.base_service import BaseBankService

logger = logging.getLogger(__name__)


class BancoBangenteService(BaseBankService):
    def __init__(self, bank_code: str = "0146", config: Dict[str, Any] = None):
        """CONSTRUCTOR - INICIALIZA EL SERVICIO DE BANGENTE
        
        ¿QUÉ HACE?
        ----------
        Es como encender el servicio de Bangente. Prepara todo lo necesario
        para que pueda funcionar correctamente.
        
        VARIABLES QUE RECIBE:
        --------------------
        - bank_code: El código del banco (por defecto 0146 para Bangente)
        - config: Configuración especial (opcional)
        
        ¿QUÉ GUARDA?
        -----------
        - self.bank_code: Guarda el código 0146 para saber que es Bangente
        """
        super().__init__(config=config)
        self.bank_code = bank_code  # Guardamos que este servicio es para Bangente (0146)

    async def consulta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """MÉTODO CONSULTA - RESPONDE PREGUNTAS SOBRE TASA DE CAMBIO
        
        ¿QUÉ HACE?
        ----------
        Cuando Bangente pregunta cuál es la tasa del dólar, este método
        le responde con la información solicitada.
        
        INFORMACIÓN QUE RECIBE (payload):
        ----------------------------------
        - Moneda: Tipo de moneda (ej: USD, EUR)
        - Fechavalor: Fecha para consultar (ej: 2024-11-14)
        
        INFORMACIÓN QUE DEVUELVE:
        -------------------------
        - code: Código de respuesta (00 = éxito, 01 = error)
        - fechavalor: La fecha que se consultó
        - tipocambio: El precio del dólar (actualmente 0.0)
        
        EJEMPLO:
        --------
        Bangente envía: {"Moneda": "USD", "Fechavalor": "2024-11-14"}
        Este método responde: {"code": "00", "fechavalor": "2024-11-14", "tipocambio": 0.0}
        """
        # Registrar en el log que Bangente hizo una consulta
        logger.debug(f"[{self.bank_code}] consulta payload: {payload}")
        
        # Preparar la respuesta para Bangente
        return {
            "code": "00",  # Código de éxito
            "fechavalor": payload.get("Fechavalor", ""),  # Devolver la fecha que pidieron
            "tipocambio": 0.0  # Tasa actual (por ahora 0.0)
        }

    async def respuesta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """MÉTODO RESPUESTA - PROCESA NOTIFICACIONES DE PAGOS
        
        ¿QUÉ HACE?
        ----------
        Cuando Bangente nos notifica que alguien nos envió un pago móvil,
        este método decide si aceptamos o rechazamos el pago.
        
        INFORMACIÓN QUE RECIBE (payload):
        ----------------------------------
        - IdComercio: Nuestra cédula como comercio
        - TelefonoEmisor: Teléfono de quien nos pagó
        - Monto: Cantidad de dinero recibida
        - Referencia: Número único del pago
        - CodigoRed: Código que indica si el pago fue exitoso
        
        INFORMACIÓN QUE DEVUELVE:
        -------------------------
        - abono: Si aceptamos el pago (true) o lo rechazamos (false)
        - mensaje: Explicación del resultado
        - codigo: Código numérico (0 = pendiente, 1 = aceptado, -1 = rechazado)
        
        EJEMPLO:
        --------
        Bangente nos dice: "Te enviaron 100 Bs desde el teléfono 04141234567"
        Este método responde: "No acepto el pago, está pendiente de revisión"
        """
        # Registrar en el log que Bangente nos notificó un pago
        logger.debug(f"[{self.bank_code}] respuesta payload: {payload}")
        
        # Por ahora, rechazamos todos los pagos (están pendientes)
        return {
            "abono": False,  # No aceptamos el pago
            "mensaje": "pendiente",  # Explicación: está pendiente
            "codigo": 0  # Código 0 = pendiente de revisión
        }

    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """MÉTODO PÚBLICO - CONSULTAR TASA DE CAMBIO
        
        Este es el método que se llama cuando alguien hace:
        POST /api/0146/MBbcv o POST /api/bangente/MBbcv
        
        Simplemente llama al método interno 'consulta' que hace el trabajo real.
        """
        return await self.consulta(payload)  # Delegar al método interno

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """MÉTODO PÚBLICO - PROCESAR NOTIFICACIÓN DE PAGO
        
        Este es el método que se llama cuando alguien hace:
        POST /api/0146/R4notifica o POST /api/bangente/R4notifica
        
        Simplemente llama al método interno 'respuesta' que hace el trabajo real.
        """
        return await self.respuesta(payload)  # Delegar al método interno

    async def consulta_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """MÉTODO PÚBLICO - CONSULTAR SI UN CLIENTE EXISTE
        
        Este es el método que se llama cuando alguien hace:
        POST /api/0146/R4consulta o POST /api/bangente/R4consulta
        
        Por ahora usa la misma lógica que consultar_tasa.
        En el futuro se puede personalizar para verificar clientes específicamente.
        """
        return await self.consulta(payload)  # Por ahora, usar la misma lógica
