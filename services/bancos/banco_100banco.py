"""
SERVICIO ESPECÍFICO: 100% BANCO (CÓDIGO 0156)
================================================

Este archivo define cómo hablamos con 100% Banco dentro del sistema.
Usa una lógica muy sencilla para que se entienda el flujo:

- consulta(payload): Simula una consulta de tasa u operación simple
- respuesta(payload): Simula la respuesta a una notificación de pago

Cómo leer esto si no programas:
- Imagina que el banco nos hace preguntas o nos envía avisos (pagos)
- Aquí respondemos a esas preguntas de manera estandarizada
- Este servicio se puede reemplazar en el futuro por lógica real (BD/API)

Creado por: Alicson Rubio
"""
from typing import Dict, Any
import logging
from services.bancos.base_service import BaseBankService

logger = logging.getLogger(__name__)


class Banco100bancoService(BaseBankService):
    """Servicio mínimo para 100% Banco.

    Nota: Este servicio devuelve datos "de ejemplo". En producción,
    aquí se conectaría a la base de datos o a la API del banco.
    """
    def __init__(self, bank_code: str = "0156", config: Dict[str, Any] = None):
        super().__init__(config=config)
        self.bank_code = bank_code

    async def consulta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta simple (ej: tasa BCV simulada).

        Entrada:
        - payload: Debe contener "Fechavalor" y opcionalmente "Moneda".

        Salida:
        - code: "00" si todo bien
        - fechavalor: eco de la fecha recibida
        - tipocambio: número simulado (0.0 por ser demo)
        """
        logger.debug(f"[{self.bank_code}] consulta payload: {payload}")
        return {"code": "00", "fechavalor": payload.get("Fechavalor", ""), "tipocambio": 0.0}

    async def respuesta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Respuesta a una notificación de pago (simulada).

        Entradas clave en payload (cuando sea notificación real):
        - Referencia, Monto, BancoEmisor, FechaHora, etc.

        Salida:
        - abono: False (por ser demo)
        - mensaje: Estado legible
        - codigo: Numérico simple (0 = pendiente)
        """
        logger.debug(f"[{self.bank_code}] respuesta payload: {payload}")
        return {"abono": False, "mensaje": "pendiente", "codigo": 0}

    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Atajo que reusa la consulta simple para "tasa".

        En una implementación real, aquí podrías llamar a un servicio que
        consulte la tasa del día desde el banco o una tabla de referencia.
        """
        return await self.consulta(payload)

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa notificaciones de pago (simulado).

        En producción:
        - Verifica duplicados por referencia
        - Llama a un procedimiento almacenado (SP)
        - Aplica validaciones de negocio
        """
        return await self.respuesta(payload)

    async def consulta_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta de cliente (intención de pago) reusando consulta().

        Normalmente responderíamos si el cliente existe/puede recibir pagos.
        Para demo, devolvemos estructura mínima válida.
        """
        return await self.consulta(payload)
