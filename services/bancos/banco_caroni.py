"""Servicio plantilla para Banco Caroní (código 0128).
Creado por: Alicson Rubio
"""
from typing import Dict, Any
import logging
from services.bancos.base_service import BaseBankService

logger = logging.getLogger(__name__)


class BancoCaroniService(BaseBankService):
    def __init__(self, bank_code: str = "0128", config: Dict[str, Any] = None):
        super().__init__(config=config)
        self.bank_code = bank_code

    async def consulta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"[Caroni:{self.bank_code}] consulta payload: {payload}")
        return {"code": "00", "fechavalor": payload.get("Fechavalor", ""), "tipocambio": 0.0}

    async def respuesta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"[Caroni:{self.bank_code}] respuesta payload: {payload}")
        return {"abono": False, "mensaje": "pendiente", "codigo": 0}

    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.consulta(payload)

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.respuesta(payload)

    async def consulta_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.consulta(payload)
