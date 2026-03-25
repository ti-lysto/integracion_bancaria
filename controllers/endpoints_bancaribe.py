
from fastapi import APIRouter, Body, Depends, HTTPException, Request
import logging
from typing import Dict, Any 
from core import auth
from models.schemas_bancaribe import (
    BancaribenotificationsRequest,
    BancaribenotificationsResponse,
)

logger = logging.getLogger(__name__)


router_bancaribe = APIRouter(prefix="/bancaribe", tags=["Bancaribe"])

try:
    from services.bancos.banco_bancaribe import BancoBancaribeService
except Exception as exc:
    BancoBancaribeService = None
    _bancaribe_import_error = exc
else:
    _bancaribe_import_error = None


_bancaribe_service = None


def _get_bancaribe_service():
    """Inicializa el servicio una sola vez y valida que esté disponible."""
    global _bancaribe_service

    if BancoBancaribeService is None:
        detail = (
            "Servicio Bancaribe no disponible. "
            f"Error de importacion: {_bancaribe_import_error}"
        )
        logger.error(detail)
        raise HTTPException(status_code=500, detail=detail)

    if _bancaribe_service is None:
        _bancaribe_service = BancoBancaribeService()

    return _bancaribe_service

@router_bancaribe.post("/token", summary="Bancaribe - Generar token de autenticación")
async def bancaribe_token():
    try:
        service = _get_bancaribe_service()
        token_result = await service.solicito_token()
        return {**token_result} if token_result else {}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error al generar token de Bancaribe: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@router_bancaribe.post("/notifications", response_model=BancaribenotificationsResponse, summary="Bancaribe - Notificación de Transacciones")
async def bancaribe_notifications(
    payload: BancaribenotificationsRequest = Body(...),#payload: Dict[str, Any] = Body(...),   #payload: BancaribenotificationsRequest = Body(...),
    _ip=Depends(auth.ip_whitelist_middleware),
):
    try:
        service = _get_bancaribe_service()
        resultado = await service.procesar_notificacion(payload.dict() if isinstance(payload, BancaribenotificationsRequest) else payload)
        return BancaribenotificationsResponse(**resultado)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error en Bancaribe /notifications: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@router_bancaribe.post("/consultaoperaciones", summary="Bancaribe - Consulta de operaciones")#response_model=BancaribenotificationsResponse, summary="Bancaribe - Consulta de operaciones")
async def bancaribe_consulta_operaciones(
    payload: Dict[str, Any] = Body(...),#payload: Dict[str, Any] = Body(...),   #payload: BancaribenotificationsRequest = Body(...),
    _ip=Depends(auth.ip_whitelist_middleware),
):
    try:
        service = _get_bancaribe_service()
        #resultado = await service.procesar_notificacion(payload.dict() if isinstance(payload, BancaribenotificationsRequest) else payload)
        resultado = await service.consulta_operaciones(payload)
        #return BancaribenotificationsResponse(**resultado)
        return (resultado)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error en Bancaribe /consultaoperaciones: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))



