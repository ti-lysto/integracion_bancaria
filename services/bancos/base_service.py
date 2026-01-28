"""
BASE/INTERFAZ DE SERVICIOS BANCARIOS
====================================

Este archivo define una "plantilla" que todos los bancos deben seguir.
Piensa en esto como un contrato: si un banco quiere integrarse, tiene que
ofrecer estas mismas "puertas" (métodos) para que el sistema sepa cómo hablarle.

¿Por qué existe esta base?
- Para que todos los bancos funcionen igual desde el punto de vista de la API
- Para poder cambiar un banco sin romper el resto del sistema
- Para que el equipo sepa exactamente qué métodos implementar

Qué debe implementar cada banco (mínimo):
- consultar_tasa(payload): Devuelve la tasa de cambio o información similar
- consulta_cliente(payload): Verifica si un cliente es válido (intención de pago)
- procesar_notificacion(payload): Procesa la notificación de pago recibido

Cómo leer esto si no programas:
- Imagina que cada banco es un proveedor con el que hablamos por teléfono
- Esta clase dice qué preguntas siempre les hacemos (los métodos)
- Cada banco debe saber responder a esas preguntas de la misma forma

Creado por: Alicson Rubio
"""
from typing import Dict, Any
from abc import ABC, abstractmethod


class BaseBankService(ABC):
    """Interfaz/base para servicios por banco.

    Todas las clases de bancos deben heredar de esta clase y completar
    los métodos marcados como "abstractos" (obligatorios). Así garantizamos
    que todos los bancos hablen el mismo idioma con nuestra API.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    async def consultar_tasa(self, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Consultar tasa o información del banco.

        Entrada (payload):
        - Diccionario con datos que el banco requiere (ej: Moneda, Fechavalor).

        Salida:
        - Diccionario con "code" (resultado), "fechavalor" y "tipocambio".
        """
    
    @abstractmethod
    async def consulta_cliente(self, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Consultar información del cliente.

        ¿Para qué sirve?
        - Es la etapa de INTENCIÓN de pago: el banco pregunta si aceptamos
          cobrar a un cliente antes de ejecutar el pago.

        Salida típica:
        - {"status": true|false}
        """

    @abstractmethod
    async def procesar_notificacion(self, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Procesar una notificación de pago (notifica/confirmación).

        ¿Qué hace?
        - Recibe del banco los datos del pago ya realizado
        - Guarda/valida en base de datos según tus reglas
        - Devuelve si se abonó o no (por duplicados, errores, etc.)

        Salida típica:
        - {"abono": true|false, "mensaje": str, "codigo": int}
        """

    @abstractmethod
    async def procesar_vuelto(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar la verificación de un vuelto (estado de la transacción).
        Entrada:
        - Datos de la transacción (referencia, monto, etc.)
        Salida típica:
        - {"code": str, "message": str, "reference": str}
        """
        
