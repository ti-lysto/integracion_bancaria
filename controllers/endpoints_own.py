
from fastapi import APIRouter, HTTPException, Request, Body, Depends
from core import auth
from core.config import Config
import logging
from db.connector import test_connection
from typing import Dict, Any
from pydantic import BaseModel
#from controllers.endpoints_r4 import router_r4
#from controllers.endpoints_bancaribe import router_bancaribe
from services.api_service import ApiService
from fastapi.routing import APIRoute

# CONFIGURACIÓN DEL ROUTER
# ========================
# Esto es como el "organizador" de todas nuestras rutas/URLs
router = APIRouter(prefix="", tags=["integracion"])
logger = logging.getLogger(__name__)

class reportar_pago_request(BaseModel):
    """Modelo para la solicitud de reportar pago"""
    banco_own: str  # código del banco receptor del pago

    banco_emisor: str  # código del banco emisor del pago
    transaction_id: str
    amount: float
    currency: str
    payer_info: Dict[str, Any]  # Información del pagador (nombre, email, etc.)
    payment_method: str  # Método de pago (ej: "tarjeta", "transferencia", etc.)
    timestamp: str  # Fecha y hora del pago (formato ISO 8601)

def get_api_service():
    try:
        """Función para obtener una instancia del servicio general de la API."""
        if not ApiService:
            logger.error("ApiService no disponible")
            raise Exception("ApiService no disponible")
        return ApiService()
    except Exception as exc:
        logger.error(f"Error al obtener el servicio API: {exc}")
        raise HTTPException(status_code=500, detail="Error interno al obtener el servicio API")


# Reportar Pago - Endpoint para recibir notificaciones de pago desde la app móvil
@router.post("/ReportarPago", summary="Endpoint para reportar un pago recibido")
async def reportar_pago(
    payload: Dict[str, Any] = Body(...), #payload: reportar_pago_request = Body(...),
    _ip=Depends(auth.ip_whitelist_middleware)
):
    try:
        servicio = get_api_service()
        resultado = await servicio.procesar_reporte_pago(payload)
        logger.info(f"Recibido ReportarPago con payload: {payload}")
        # Aquí podríamos agregar lógica para procesar el pago, guardar en BD, etc.
        return resultado
    except Exception as exc:
        logger.error(f"Error procesando ReportarPago: {exc}")
        raise HTTPException(status_code=500, detail="Error interno al procesar el pago") 

# ENDPOINTS DE SISTEMA
# ====================
@router.get("/health")
async def health_check():
    
    """Verificar estado de la API"""
    try:        
        db_ok = await test_connection()
        status = "ok" if db_ok else "fail"
        if not db_ok:
            logger.error("Fallo en verificación de conexión a BD (SELECT 1)")
        
        return {
            "message": "API integracion-bancaria funcionando correctamente",
            "version": Config.API_VERSION,
            "status BD": status,
            "Conectado": db_ok,
            "endpoints_count": [
                {"Sistema": len(router.routes)},
                {"Banco R4": len(router_r4.routes)},
                {"BanCaribe": len(router_bancaribe.routes)}
            ]
        }
    except Exception as err:
        logger.exception(f"Error en health_check: {err}")
        raise HTTPException(status_code=500, detail="Health check interno falló")
    
@router.get("/")
async def root():
    """Información básica de la API"""
    try:
        return {
            "name": "API integracion-bancaria",
            "version": Config.API_VERSION,
            "bancos_soportados": {
                "Own": {
                    "cantidad_endpoints": len(router.routes),
                    "endpoints": [route.path for route in router.routes if isinstance(route, APIRoute)]
                },
                "R4 Conecta": {
                    "cantidad_endpoints": len(router_r4.routes),
                    "endpoints": [route.path for route in router_r4.routes if isinstance(route, APIRoute)]
                },
                "BanCaribe":{
                    "cantidad_endpoints": len(router_bancaribe.routes),
                    "endpoints": [route.path for route in router_bancaribe.routes if isinstance(route, APIRoute)]                
                }
            },
            "estado": "operativo"
        }
    except Exception as exc:
        logger.error(f"Error en endpoint raíz (/): {exc}")
        raise HTTPException(status_code=500, detail="Error interno al obtener información de la API")