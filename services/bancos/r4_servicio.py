"""Adaptador/consolidación de servicios por banco basados en R4.

Este módulo contiene una clase adaptadora que implementa la interfaz
`BaseBankService` y delega la lógica en `R4Services` (la lógica original).

La idea es centralizar todos los comportamientos por banco en un solo lugar
para poder personalizar por código de banco en el futuro sin tocar la
implementación base de R4.

Creado por: Alicson Rubio
"""
from typing import Dict, Any
import logging

from services.bancos.base_service import BaseBankService
from services.r4_services import R4Services
from services import r4_client
from typing import Optional

logger = logging.getLogger(__name__)


class BankR4Adapter(BaseBankService):
    """Adaptador genérico que implementa la API esperada por los routers.

    Por ahora todas las operaciones delegan a R4Services; se guarda el
    `bank_code` para logging y para futuras personalizaciones.
    """

    def __init__(self, bank_code: str = "r4", config: Dict[str, Any] = None):
        super().__init__(config=config)
        self.bank_code = bank_code

    async def consultar_tasa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consultar tasa — soporta payload tipo R4BcvRequest o genérico.

        Se espera payload con claves: Moneda, Fechavalor
        """
        try:
            
            moneda = payload.get("Moneda") or payload.get("moneda") or payload.get("Moneda".lower())
            fechavalor = payload.get("Fechavalor") or payload.get("fechavalor")
            if moneda and fechavalor:
                logger.debug(f"[{self.bank_code}] Consultando tasa para {moneda} {fechavalor}")
                return await R4Services.procesar_consulta_bcv(moneda, fechavalor)

            # Fallback: usar implementación mínima de R4
            logger.debug(f"[{self.bank_code}] Payload incompleto para consultar_tasa, usando valor por defecto")
            return {"code": "01", "fechavalor": fechavalor or "", "tipocambio": 0.0}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error consultar_tasa: {e}")
            return {"code": "01", "fechavalor": payload.get("Fechavalor", ""), "tipocambio": 0.0}

    async def procesar_notificacion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar notificación de pago.

        Delegamos al método que ya existe en R4Services: `procesar_notificacion_pago`.
        """
        try:
            logger.debug(f"[{self.bank_code}] Procesando notificación: {payload.get('Referencia') or payload.get('Referencia', '')}")
            return await R4Services.procesar_notificacion_pago(payload)
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error procesar_notificacion: {e}")
            return {"abono": False, "mensaje": str(e), "codigo": -1}

    async def procesar_gestion_pagos(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await R4Services.procesar_gestion_pagos(payload)
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error procesar_gestion_pagos: {e}")
            return {"success": False, "message": str(e)}

    async def procesar_vuelto(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await R4Services.procesar_vuelto(payload)
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error procesar_vuelto: {e}")
            return {"code": "08", "message": "Error procesando vuelto"}

    async def generar_otp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            return {"code": "202", "message": "Se ha recibido el mensaje de forma satisfactoria", "success": True}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error generar_otp: {e}")
            raise

    async def debito_inmediato(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            import uuid
            operation_id = str(uuid.uuid4())
            reference = str(uuid.uuid4().int)[:8]
            return {"code": "ACCP", "message": "Operación Aceptada", "reference": reference, "Id": operation_id}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error debito_inmediato: {e}")
            import uuid
            operation_id = str(uuid.uuid4())
            return {"code": "AC00", "message": "Operación en Espera de Respuesta del Receptor", "Id": operation_id}

    async def credito_inmediato(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            import uuid
            operation_id = str(uuid.uuid4())
            reference = str(uuid.uuid4().int)[:8]
            return {"code": "ACCP", "message": "Operación Aceptada", "reference": reference, "Id": operation_id}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error credito_inmediato: {e}")
            import uuid
            operation_id = str(uuid.uuid4())
            return {"code": "AC00", "message": "Operación en Espera de Respuesta del Receptor", "Id": operation_id}

    async def domiciliacion_cnta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            import uuid
            return {"code": "202", "message": "Se ha recibido el mensaje de forma satisfactoria", "uuid": str(uuid.uuid4())}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error domiciliacion_cnta: {e}")
            return {"code": "07", "message": "Request Inválida, error en el campo: DocId", "uuid": ""}

    async def domiciliacion_cele(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            import uuid
            return {"code": "202", "message": "Se ha recibido el mensaje de forma satisfactoria", "uuid": str(uuid.uuid4())}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error domiciliacion_cele: {e}")
            return {"code": "07", "message": "Request Inválida, error en el campo: DocId", "uuid": ""}

    async def consultar_operaciones(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import uuid
            reference = str(uuid.uuid4().int)[:8]
            return {"code": "ACCP", "reference": reference, "success": True}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error consultar_operaciones: {e}")
            raise

    async def ci_cuentas(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            import uuid
            reference = str(uuid.uuid4().int)[:8]
            return {"code": "ACCP", "message": "Operación Aceptada", "reference": reference}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error ci_cuentas: {e}")
            import uuid
            operation_id = str(uuid.uuid4())
            return {"code": "AC00", "message": "Operación en Espera de Respuesta del Receptor", "Id": operation_id}

    async def mb_c2p(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            reference = None
            try:
                import uuid
                reference = str(uuid.uuid4().int)[:8]
            except Exception:
                reference = ""
            return {"code": "00", "message": "TRANSACCION EXITOSA", "reference": reference}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error mb_c2p: {e}")
            return {"code": "08", "message": "TOKEN inválido"}

    async def mb_anulacion_c2p(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await r4_client.procesar_y_guardar(payload)
            reference = None
            try:
                import uuid
                reference = str(uuid.uuid4().int)[:8]
            except Exception:
                reference = ""
            return {"code": "00", "message": "TRANSACCION EXITOSA", "reference": reference}
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error mb_anulacion_c2p: {e}")
            return {"code": "41", "message": "Servicio no activo o negada por el banco"}

    async def verificar_pago(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await R4Services.verificar_pago(payload)
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error verificar_pago: {e}")
            return {"code": "08", "message": "Error verificando pago"}

    # Métodos adicionales para mantener compatibilidad con la capa superior
    async def consulta_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            id_cliente = payload.get("IdCliente") or payload.get("cliente_id")
            monto = payload.get("Monto")
            telefono = payload.get("TelefonoComercio")
            return await R4Services.procesar_consulta_cliente(id_cliente, monto, telefono)
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error consulta_cliente: {e}")
            return {"status": False}


def BankServiceFactory(bank_code: str) -> BankR4Adapter:
    """Factory simple que devuelve una instancia del adaptador para el banco."""
    return BankR4Adapter(bank_code=bank_code)
