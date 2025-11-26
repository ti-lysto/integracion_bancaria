"""Implementación del servicio R4.
Basado en la lógica existente, este archivo agrupa funciones específicas
para R4 y adapta la interfaz de BaseBankService.
Creado por: Alicson Rubio
"""
from typing import Dict, Any
from services.bancos.base_service import BaseBankService
import logging

logger = logging.getLogger(__name__)


class R4Service(BaseBankService):
    """Servicio R4 - implementación mínima"""

    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Implementar consulta BCV u otra lógica según documentación
        logger.debug("R4Service.consultar_tasa called")
        return {"code": "00", "fechavalor": payload.get("Fechavalor"), "tipocambio": 36.5314}

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Delegar a la lógica existente (repository/SP) — aquí solo un ejemplo
        logger.debug("R4Service.procesar_notificacion called")
        # TODO: llamar a app.db.repository.guardar_transaccion_sp
        return {"success": True, "code": 1, "message": "Notificación procesada (simulada)"}
