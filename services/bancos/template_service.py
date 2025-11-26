"""Plantilla para crear un servicio por banco.

Copia este archivo y renómbralo a e.g. `banesco_service.py`.
Implementa solo las diferencias respecto al adaptador por defecto.

Ejemplo de uso:
    class BanescoService(BaseBankService):
        async def procesar_notificacion(self, payload):
            # adaptar payload, llamar SP específico, etc.
            return await super().procesar_notificacion(payload)

"""
from typing import Dict, Any
import logging
from services.bancos.base_service import BaseBankService
from services.bancos.r4_servicio import BankR4Adapter

logger = logging.getLogger(__name__)


class TemplateBankService(BankR4Adapter):
    """Servicio base para un banco específico.

    Hereda de BankR4Adapter para reutilizar la lógica R4 y sobreescribir
    solo lo necesario (HMAC, SP, validaciones, etc.).
    """

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Validaciones específicas del banco
        # e.g.: payload['Monto'] = convertir_formato(payload['Monto'])

        # Llamar al método base (delegará a R4Services por defecto)
        result = await super().procesar_notificacion(payload)

        # Post-procesamiento específico si se requiere
        return result


def factory(bank_code: str) -> TemplateBankService:
    return TemplateBankService(bank_code=bank_code)
