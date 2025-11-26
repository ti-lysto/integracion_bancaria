"""Servicio específico para el banco R4 (versión en español).

Define dos métodos públicos: `consulta` y `respuesta`.

Creado por: Alicson Rubio
"""
from typing import Dict, Any
import logging
from services.bancos.base_service import BaseBankService
from services.bancos.r4_servicio import BankR4Adapter

logger = logging.getLogger(__name__)


class BancoR4Service(BaseBankService):
    def __init__(self, bank_code: str = "r4", config: Dict[str, Any] = None):
        super().__init__(config=config)
        self.bank_code = bank_code
        # mantener un adaptador interno que implementa la lógica real
        self._adapter = BankR4Adapter(bank_code=bank_code, config=config)

    async def consulta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"[{self.bank_code}] consulta delegando a BankR4Adapter: {payload}")
        # Delegar a la implementación real de R4
        return await self._adapter.consultar_tasa(payload)

    async def respuesta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"[{self.bank_code}] respuesta delegando a BankR4Adapter: {payload}")
        return await self._adapter.procesar_notificacion(payload)

    # Implementación de la interfaz/base
    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.consulta(payload)

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.respuesta(payload)

    async def consulta_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Método requerido por la interfaz - delega a consulta existente"""
        return await self.consulta(payload)
