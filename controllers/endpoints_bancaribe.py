
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
        token_result = await service.solicito_token({})
        return {**token_result} if token_result else {}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error al generar token de Bancaribe: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@router_bancaribe.post("/notifications", response_model=BancaribenotificationsResponse, summary="Bancaribe - Notificación de Transacciones")
async def bancaribe_notifications(
    payload: BancaribenotificationsRequest = Body(...),#payload: Dict[str, Any] = Body(...),   #payload: BancaribenotificationsRequest = Body(...),
    #_ip=Depends(auth.ip_whitelist_middleware),
):
    try:
        service = _get_bancaribe_service()
        resultado = await service.procesar_notificacion(payload.dict() if isinstance(payload, BancaribenotificationsRequest) else payload)
        return BancaribenotificationsResponse(**resultado)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error en Bancaribe MBbcv: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# @router_bancaribe.post("/R4consulta", response_model=R4ConsultaResponse, summary="Bancaribe - Consulta de cliente")
# async def bancaribe_r4consulta(
#     payload: R4ConsultaRequest = Body(...),
#     request: Request = None,
#     _ip=Depends(auth.ip_whitelist_middleware),
# ):
#     try:
#         service = _get_bancaribe_service()
#         resultado = await service.consulta_cliente(payload.dict())

#         # Si el servicio no devuelve "status", aplicamos una conversión segura.
#         if "status" in resultado:
#             status_value = bool(resultado.get("status"))
#         else:
#             code = str(resultado.get("code", ""))
#             status_value = code == "00"

#         if request is not None:
#             logger.info(
#                 "Bancaribe consulta cliente %s en %s -> %s",
#                 payload.IdCliente,
#                 request.scope["route"].path,
#                 status_value,
#             )

#         return R4ConsultaResponse(status=status_value)
#     except HTTPException:
#         raise
#     except Exception as exc:
#         logger.error(f"Error en Bancaribe R4consulta: {exc}")
#         raise HTTPException(status_code=500, detail=str(exc))


# @router_bancaribe.post("/R4notifica", response_model=R4NotificaResponse, summary="Bancaribe - Notificacion de pago")
# async def bancaribe_r4notifica(
#     payload: R4NotificaRequest = Body(...),
#     _ip=Depends(auth.ip_whitelist_middleware),
# ):
#     try:
#         service = _get_bancaribe_service()
#         resultado = await service.procesar_notificacion(payload.dict())

#         if "abono" in resultado:
#             abono = bool(resultado.get("abono"))
#         else:
#             code = str(resultado.get("code", ""))
#             abono = code == "00"

#         return R4NotificaResponse(abono=abono)
#     except HTTPException:
#         raise
#     except Exception as exc:
#         logger.error(f"Error en Bancaribe R4notifica: {exc}")
#         raise HTTPException(status_code=500, detail=str(exc))
