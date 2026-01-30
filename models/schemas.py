"""
ESQUEMAS Y MODELOS DE DATOS PARA LA API R4 CONECTA
==================================================

Este archivo define todos los "moldes" o "formatos" que deben tener los datos
que entran y salen de nuestra API.

¿Qué son los esquemas?
- Son como "plantillas" que definen cómo deben verse los datos
- Especifican qué campos son obligatorios y cuáles opcionales
- Validan que los datos tengan el formato correcto
- Convierten automáticamente los tipos de datos

¿Por qué son importantes?
- Garantizan que todos los datos sean consistentes
- Previenen errores por datos mal formateados
- Facilitan la documentación automática de la API
- Mejoran la seguridad al validar entradas

Creado por: Alicson Rubio
Fecha: 11/2025
"""

# IMPORTACIONES NECESARIAS
# ========================
from pydantic import BaseModel, Field, model_validator, ConfigDict
# BaseModel: Clase base para crear esquemas de datos
# Field: Para agregar validaciones y descripciones a los campos

from typing import Optional, Dict, Any
# Optional: Para campos que pueden ser nulos
# Dict: Para diccionarios (clave-valor)
# Any: Para cualquier tipo de dato


# # ESQUEMA GENÉRICO DE INTEGRACIÓN
# # ===============================
# class IntegracionPayload(BaseModel):
#     """
#     MODELO GENÉRICO PARA CUALQUIER TRANSACCIÓN DE R4
    
#     ¿Qué es?
#     - Un formato flexible para recibir cualquier tipo de datos de R4
#     - Se usa cuando no tenemos un esquema específico
#     - Permite campos adicionales según la necesidad
    
#     ¿Cuándo se usa?
#     - Para el endpoint /integrar (genérico)
#     - Para operaciones nuevas que aún no tienen esquema específico
#     - Como respaldo cuando otros esquemas no aplican
    
#     Campos:
#     - id_operacion: Identificador único que asigna R4 a cada operación
#     - monto: Cantidad de dinero involucrada en la transacción
#     - moneda: Tipo de moneda (USD, VES, EUR, etc.) - por defecto USD
#     - cliente_id: Identificación del cliente involucrado (opcional)
#     - metadatos: Información adicional en formato libre (opcional)
#     """
    
#     # Campo obligatorio: ID único de la operación
#     id_operacion: str = Field(
#         ...,  # Los tres puntos (...) significan "obligatorio"
#         description="ID único de la operación en R4"
#     )
    
#     # Campo obligatorio: Monto de la transacción
#     monto: float = Field(
#         ..., 
#         description="Monto de la transacción"
#     )
    
#     # Campo opcional: Tipo de moneda (por defecto USD)
#     moneda: Optional[str] = Field(
#         "USD",  # Valor por defecto
#         description="Código de moneda"
#     )
    
#     # Campo opcional: ID del cliente
#     cliente_id: Optional[str] = Field(
#         None,  # None significa que puede estar vacío
#         description="Identificador del cliente"
#     )
    
#     # Campo opcional: Datos adicionales
#     metadatos: Optional[Dict[str, Any]] = Field(
#         None, 
#         description="Campos libres adicionales"
#     )


# ESQUEMAS PARA CONSULTA DE TASA BCV
# ==================================
class R4BcvRequest(BaseModel):
    """
    DATOS QUE RECIBIMOS PARA CONSULTAR LA TASA DEL BCV
    
    ¿Qué es el BCV?
    - Banco Central de Venezuela
    - Entidad que establece la tasa de cambio oficial del dólar
    
    ¿Para qué sirve esta consulta?
    - Para saber cuántos bolívares vale un dólar oficialmente
    - Para hacer conversiones de moneda precisas
    - Para cumplir con regulaciones cambiarias
    
    Campos requeridos:
    - Moneda: Código ISO de la moneda (ej: "USD", "EUR")
    - Fechavalor: Fecha para la cual queremos la tasa (formato: YYYY-MM-DD)
    """
    
    Moneda: str  # Código de moneda (obligatorio)
    Fechavalor: str  # Fecha en formato YYYY-MM-DD (obligatorio)


class R4BcvResponse(BaseModel):
    """
    RESPUESTA QUE ENVIAMOS CON LA TASA DEL BCV
    
    ¿Qué devolvemos?
    - El código de resultado de la operación
    - La fecha consultada (confirmación)
    - El valor de la tasa de cambio
    
    Ejemplo de respuesta:
    {
        "code": "00",
        "fechavalor": "2024-01-15", 
        "tipocambio": 36.5314
    }
    
    Esto significa: El 15 de enero de 2024, 1 USD = 36.5314 VES
    """
    
    code: str  # Código de resultado ("00" = exitoso)
    fechavalor: str  # Fecha consultada
    tipocambio: float  # Valor de la tasa de cambio


# ESQUEMAS PARA CONSULTA DE CLIENTE
# =================================
class R4ConsultaRequest(BaseModel):
    """
    DATOS PARA CONSULTAR SI UN CLIENTE PUEDE RECIBIR PAGOS
    
    ¿Qué es esta consulta?
    - El banco nos pregunta si conocemos a un cliente
    - Verificamos si está registrado en nuestro sistema
    - Decidimos si puede recibir el monto solicitado
    
    ¿Por qué es importante?
    - Evita pagos a personas equivocadas
    - Permite validar límites de recepción
    - Mejora la seguridad de las transacciones
    
    Campos:
    - IdCliente: Cédula o identificación del cliente (obligatorio)
    - Monto: Cantidad que quiere recibir (opcional)
    - TelefonoComercio: Nuestro teléfono registrado (opcional)
    """
    
    IdCliente: str  # Cédula del cliente (obligatorio)
    Monto: Optional[str]  # Monto a recibir (opcional)
    TelefonoComercio: Optional[str]  # Nuestro teléfono (opcional)


class R4ConsultaResponse(BaseModel):
    """
    RESPUESTA A LA CONSULTA DE CLIENTE
    
    ¿Qué respondemos?
    - true: Sí conocemos al cliente y puede recibir el pago
    - false: No lo conocemos o no puede recibir el pago
    
    Esta respuesta determina si el banco procede con el pago o lo rechaza.
    """
    
    status: bool  # true = acepta, false = rechaza


# ESQUEMAS PARA NOTIFICACIÓN DE PAGO
# ==================================
class R4NotificaRequest(BaseModel):
    """
    DATOS QUE RECIBIMOS CUANDO NOS LLEGA UN PAGO MÓVIL
    
    ¿Qué es esta notificación?
    - El banco nos informa que alguien nos envió dinero
    - Incluye todos los detalles de la transacción
    - Nosotros guardamos en la base de datos
    
    ¿Cuándo llega?
    - Después de que alguien hace un pago móvil mediante la plataforma R4
    - Antes de que cliente reporte el pago
    
    Campos importantes:
    - IdComercio: Identificador del comercio
    - TelefonoComercio: Teléfono registrado
    - TelefonoEmisor: Teléfono de quien envió el pago
    - Concepto: Descripción del pago
    - BancoEmisor: Banco de quien envía
    - Monto: Cantidad enviada
    - FechaHora: Cuándo se hizo el pago
    - Referencia: Número único de la transacción
    - CodigoRed: Código que indica si el pago fue exitoso
    """
    
    IdComercio: str  # cédula/RIF
    TelefonoComercio: str  # Teléfono comercio
    TelefonoEmisor: str  # Teléfono del que envía
    Concepto: str  # Descripción del pago
    BancoEmisor: str  # Código del banco emisor
    Monto: str  # Cantidad enviada
    FechaHora: str  # Fecha y hora del pago
    Referencia: str  # Número de referencia único
    CodigoRed: str  # Código de resultado


class R4NotificaResponse(BaseModel):
    """
    RESPUESTA A LA NOTIFICACIÓN DE PAGO
    
    ¿Qué respondemos?
    - Solo guardamos en la base de datos y agregamos abono: true si todo esta bien , false hubo un error
    
    
    """
    
    abono: bool  # true = todo bien, false = error


# ESQUEMAS PARA GESTIÓN DE PAGOS (DISPERSIÓN)
# ===========================================
class PersonaPago(BaseModel):
    """
    INFORMACIÓN DE UNA PERSONA QUE RECIBIRÁ DINERO EN LA DISPERSIÓN
    
    ¿Qué es?
    - Datos de un beneficiario individual
    - Se usa dentro de una lista de personas
    - Cada persona tiene su monto específico
    
    Campos:
    - nombres: Nombre completo del beneficiario
    - documento: Cédula con tipo (V12345678, E87654321, etc.)
    - destino: Número de cuenta bancaria (20 dígitos)
    - montoPart: Cantidad que le corresponde a esta persona
    """
    
    nombres: str  # Nombre completo
    documento: str  # Cédula con tipo
    destino: str  # Cuenta bancaria
    montoPart: str  # Monto individual


class R4PagosRequest(BaseModel):
    """
    DATOS PARA HACER PAGOS MÚLTIPLES (DISPERSIÓN)
    
    ¿Qué es dispersión?
    - Tomar un monto total y repartirlo entre varias personas
    - Como pagar nómina: 10,000 Bs repartidos entre 5 empleados
    - Se hace todo en una sola operación
    
    Ejemplo práctico:
    - monto: "1000.00" (total a repartir)
    - personas: [
        {nombres: "Juan Pérez", documento: "V12345678", destino: "01020000000000000001", montoPart: "600.00"},
        {nombres: "María García", documento: "V87654321", destino: "01340000000000000002", montoPart: "400.00"}
    ]
    
    Validación importante:
    - La suma de montoPart debe ser igual al monto total
    - Si no coincide, la operación se rechaza
    
    Campos:
    - monto: Cantidad total a dispersar
    - fecha: Fecha del pago (formato MM/DD/YYYY)
    - Referencia: Número de referencia único
    - personas: Lista de beneficiarios
    """
    
    monto: str  # Monto total
    fecha: str  # Fecha en MM/DD/YYYY
    Referencia: str  # Referencia única
    personas: list[PersonaPago]  # Lista de beneficiarios


# ESQUEMAS PARA VUELTO
# ===================
class R4VueltoRequest(BaseModel):
    """
    DATOS PARA ENVIAR VUELTO A UN CLIENTE
    
    ¿Qué es vuelto?
    - Dinero que devolvemos al cliente
    - Como cuando paga de más y le devolvemos la diferencia
    - Se envía mediante pago móvil
    
    Ejemplo:
    - Cliente pagó 100 Bs por producto de 80 Bs
    - Le enviamos 20 Bs de vuelto
    
    Campos obligatorios:
    - TelefonoDestino: Teléfono del cliente
    - Cedula: Cédula del cliente (con tipo: V, E, J, P)
    - Banco: Código del banco del cliente
    - Monto: Cantidad a devolver
    
    Campos opcionales:
    - Concepto: Descripción del vuelto
    - Ip: Dirección IP desde donde se hace la operación
    """
    
    TelefonoDestino: str  # Teléfono del cliente
    Cedula: str  # Cédula con tipo
    Banco: str  # Código del banco
    Monto: str  # Cantidad a devolver
    Concepto: Optional[str] = None  # Descripción (opcional)
    Ip: Optional[str] = None  # IP de origen (opcional)


# ESQUEMAS PARA GENERACIÓN DE OTP
# ===============================
class GenerarOtpRequest(BaseModel):
    """
    DATOS PARA SOLICITAR GENERACIÓN DE CÓDIGO OTP
    
    ¿Qué es OTP?
    - One Time Password (Contraseña de Un Solo Uso)
    - Código numérico temporal (ej: 123456)
    - Se envía por SMS al cliente
    - Solo sirve una vez y por tiempo limitado
    
    ¿Para qué se usa?
    - Para confirmar operaciones de débito
    - Como medida de seguridad adicional
    - Para verificar la identidad del cliente
    
    Proceso:
    1. Enviamos esta solicitud
    2. El banco genera el código
    3. El banco envía SMS al cliente
    4. El cliente nos dice el código
    5. Usamos el código en la siguiente operación
    
    Campos:
    - Banco: Código del banco del cliente
    - Monto: Cantidad que se va a debitar
    - Telefono: Teléfono donde se enviará el SMS
    - Cedula: Cédula del cliente
    """
    
    Banco: str  # Código del banco
    Monto: str  # Monto a debitar
    Telefono: str  # Teléfono para SMS
    Cedula: str  # Cédula del cliente

class GenerarOtpResponse(BaseModel):
    
    code: str  # codigo de resultado del banco
    message: str  # Mensaje descriptivo del banco
    success: bool  # exitoso o fallido
    


# ESQUEMAS PARA DÉBITO INMEDIATO
# ==============================
class DebitoInmediatoRequest(BaseModel):
    """
    DATOS PARA COBRAR DINERO DIRECTAMENTE AL CLIENTE
    
    ¿Qué es débito inmediato?
    - Descontar dinero de la cuenta del cliente
    - Requiere autorización previa (OTP)
    - Es como un cargo automático
    
    ¿Cuándo se usa?
    - Para cobrar servicios automáticamente
    - Para domiciliaciones bancarias
    - Para pagos recurrentes
    
    IMPORTANTE:
    - Requiere OTP válido del cliente
    - Es una operación irreversible
    - Debe usarse con máxima precaución
    
    Campos:
    - Banco: Código del banco del cliente
    - Monto: Cantidad a debitar
    - Telefono: Teléfono del cliente
    - Cedula: Cédula del cliente
    - Nombre: Nombre completo del cliente
    - OTP: Código que recibió por SMS
    - Concepto: Descripción del cobro
    """
    
    Banco: str  # Código del banco
    Monto: str  # Cantidad a debitar
    Telefono: str  # Teléfono del cliente
    Cedula: str  # Cédula del cliente
    Nombre: str  # Nombre completo
    OTP: str  # Código de autorización
    Concepto: str  # Descripción del cobro


# ESQUEMAS PARA CRÉDITO INMEDIATO
# ===============================
class CreditoInmediatoRequest(BaseModel):
    """
    DATOS PARA ENVIAR DINERO DIRECTAMENTE AL CLIENTE
    
    ¿Qué es crédito inmediato?
    - Depositar dinero en la cuenta del cliente
    - Es como hacer una transferencia instantánea
    - El dinero llega inmediatamente
    
    ¿Cuándo se usa?
    - Para pagar a proveedores
    - Para enviar reembolsos
    - Para transferir ganancias
    - Para pagos de nómina
    
    Diferencia con pago móvil:
    - Pago móvil: Se envía al teléfono, el cliente debe aceptar
    - Crédito inmediato: Se deposita directo en la cuenta
    
    Campos:
    - Banco: Código del banco del beneficiario
    - Cedula: Cédula del beneficiario
    - Telefono: Teléfono del beneficiario
    - Monto: Cantidad a enviar
    - Concepto: Descripción del pago
    """
    
    Banco: str  # Código del banco
    Cedula: str  # Cédula del beneficiario
    Telefono: str  # Teléfono del beneficiario
    Monto: str  # Cantidad a enviar
    Concepto: str  # Descripción del pago


# ESQUEMAS PARA DOMICILIACIÓN POR CUENTA
# ======================================
class DomiciliacionCNTARequest(BaseModel):
    """
    DATOS PARA CONFIGURAR COBRO AUTOMÁTICO POR CUENTA
    
    ¿Qué es domiciliación?
    - Autorización para cobrar automáticamente
    - Como cuando el banco cobra la mensualidad de la tarjeta
    - El cliente autoriza una vez, nosotros cobramos cuando queramos
    
    ¿Cómo funciona?
    1. Cliente nos autoriza cobrar de su cuenta
    2. Registramos su cuenta con este endpoint
    3. Cada mes cobramos automáticamente
    4. No necesita aprobar cada cobro individual
    
    Campos:
    - docId: Cédula del titular de la cuenta
    - nombre: Nombre completo del titular
    - cuenta: Número de cuenta bancaria (20 dígitos)
    - monto: Cantidad autorizada a cobrar
    - concepto: Descripción del servicio a cobrar
    """
    
    docId: str  # Cédula del titular
    nombre: str  # Nombre completo
    cuenta: str  # Número de cuenta (20 dígitos)
    monto: str  # Monto autorizado
    concepto: str  # Descripción del servicio


# ESQUEMAS PARA DOMICILIACIÓN POR TELÉFONO
# ========================================
class DomiciliacionCELERequest(BaseModel):
    """
    DATOS PARA CONFIGURAR COBRO AUTOMÁTICO POR TELÉFONO
    
    ¿Qué diferencia tiene con la domiciliación por cuenta?
    - Usa el teléfono en lugar del número de cuenta
    - Más fácil para el cliente (solo necesita su teléfono)
    - Funciona con pago móvil
    
    NOTA IMPORTANTE:
    - El primer envío es solo para afiliación
    - No genera cobro inmediato
    - El cliente debe confirmar en su banco primero
    
    Proceso:
    1. Enviamos solicitud de afiliación
    2. Cliente va a su banco y autoriza
    3. Una vez autorizado, podemos cobrar automáticamente
    
    Campos:
    - docId: Cédula del cliente
    - telefono: Teléfono registrado en pago móvil
    - nombre: Nombre completo del cliente
    - banco: Código del banco del cliente
    - monto: Cantidad autorizada a cobrar
    - concepto: Descripción del servicio
    """
    
    docId: str  # Cédula del cliente
    telefono: str  # Teléfono para pago móvil
    nombre: str  # Nombre completo
    banco: str  # Código del banco
    monto: str  # Monto autorizado
    concepto: str  # Descripción del servicio


# ESQUEMAS PARA CONSULTA DE OPERACIONES
# =====================================
class ConsultarOperacionesRequest(BaseModel):
    """
    DATOS PARA CONSULTAR EL ESTADO DE UNA OPERACIÓN
    
    ¿Para qué sirve?
    - Verificar si una operación anterior ya se completó
    - Obtener el resultado final de operaciones en espera
    - Confirmar si un pago ya se procesó
    
    ¿Cuándo se usa?
    - Cuando una operación respondió "AC00" (en espera)
    - Para verificar débitos o créditos pendientes
    - Para hacer seguimiento de transacciones
    
    Campo:
    - Id: Identificador único de la operación a consultar
          (es el UUID que devolvió la operación original)
    """
    
    Id: str  # Identificador único de la operación


# ESQUEMAS PARA CRÉDITO INMEDIATO CON CUENTAS
# ===========================================
class CICuentasRequest(BaseModel):
    """
    DATOS PARA CRÉDITO INMEDIATO USANDO NÚMERO DE CUENTA
    
    ¿Qué diferencia tiene con el crédito inmediato normal?
    - Usa el número de cuenta en lugar del teléfono
    - Más preciso y directo
    - No depende del pago móvil
    
    ¿Cuándo se usa?
    - Para transferencias empresariales
    - Cuando necesitamos máxima precisión
    - Para cuentas que no tienen pago móvil activo
    
    Campos:
    - Cedula: Cédula del beneficiario
    - Cuenta: Número de cuenta completo (20 dígitos)
    - Monto: Cantidad a enviar
    - Concepto: Descripción del pago
    """
    
    Cedula: str  # Cédula del beneficiario
    Cuenta: str  # Número de cuenta (20 dígitos)
    Monto: str  # Cantidad a enviar
    Concepto: str  # Descripción del pago


# ESQUEMAS PARA COBRO C2P
# =======================
class R4C2PRequest(BaseModel):
    """
    DATOS PARA COBRO DIRECTO AL CLIENTE (C2P)
    
    ¿Qué es C2P?
    - C2P = Client to Person (Cliente a Persona)
    - Es cuando nosotros le cobramos directamente al cliente
    - Similar al débito, pero con proceso diferente
    
    ¿Cuándo se usa?
    - Para cobros en punto de venta
    - Para servicios que requieren pago inmediato
    - Como alternativa al débito inmediato
    
    Campos:
    - TelefonoDestino: Teléfono del cliente
    - Cedula: Cédula del cliente
    - Concepto: Descripción del cobro
    - Banco: Código del banco del cliente
    - Ip: Dirección IP desde donde se hace
    - Monto: Cantidad a cobrar
    - Otp: Código de autorización del cliente
    """
    
    TelefonoDestino: str  # Teléfono del cliente
    Cedula: str  # Cédula del cliente
    Concepto: str  # Descripción del cobro
    Banco: str  # Código del banco
    Ip: str  # Dirección IP
    Monto: str  # Cantidad a cobrar
    Otp: str  # Código OTP del cliente


# ESQUEMAS PARA ANULACIÓN C2P
# ===========================
class R4AnulacionC2PRequest(BaseModel):
    """
    DATOS PARA ANULAR UN COBRO C2P
    
    ¿Qué hace?
    - Cancela un cobro C2P que ya se hizo
    - Devuelve el dinero al cliente
    - Es como un "reverso" de la operación
    
    ¿Cuándo se usa?
    - Cuando hubo un error en el cobro
    - Para cancelar transacciones duplicadas
    - Cuando el cliente solicita anulación
    
    IMPORTANTE:
    - Solo se pueden anular operaciones recientes
    - Debe tener la referencia exacta del cobro original
    
    Campos:
    - Cedula: Cédula del cliente original
    - Banco: Código del banco del cliente
    - Referencia: Número de referencia del cobro a anular
    """
    
    Cedula: str  # Cédula del cliente
    Banco: str  # Código del banco
    Referencia: str  # Referencia del cobro a anular


# ESQUEMAS PARA VERIFICACIÓN DE PAGO
# ==================================
class VerificoPagoRequest(BaseModel):
    """Datos de entrada para /verifico_pago — parámetros del SP.

    Solo incluye los IN esperados por `sp_consulta_notificacion_r4`.
    """

    Telefono: Optional[str] = None
    Banco: Optional[str] = None
    Monto: Optional[str] = None
    FechaHora: Optional[str] = None
    Referencia: Optional[str] = None

# ESQUEMAS PARA COMPROBACIÓN DE PAGO
# ==================================
class ComprueboPagoRequest(BaseModel):
    """Datos de entrada para /verifico_pago — parámetros del SP.

    Solo incluye los IN esperados por `sp_consulta_notificacion_r4`.
    """

    Telefono: Optional[str] = None
    Banco: Optional[str] = None
    Monto: Optional[str] = None
    FechaHora: Optional[str] = None
    Referencia: Optional[str] = None

class ComprueboPagoResponse(BaseModel):
    """Respuesta simplificada solicitada: campos del registro y flag `encontrado`."""
    
    procesado: bool = False
    mensaje: str = ""

class VerificoPagoResponse(BaseModel):
    """Respuesta simplificada solicitada: campos del registro y flag `encontrado`."""

    Telefono: str = ""
    Banco: str = ""
    Monto: str = ""
    FechaHora: str = ""
    Referencia: str = ""
    encontrado: bool = False


# ESQUEMAS DE RESPUESTAS GENÉRICAS
# ================================
class StandardResponse(BaseModel):
    """
    FORMATO ESTÁNDAR PARA LA MAYORÍA DE RESPUESTAS
    
    ¿Qué es?
    - Un formato común que usan muchos endpoints
    - Incluye los campos más comunes de respuesta
    - Facilita el manejo consistente de respuestas
    
    Campos:
    - code: Código de resultado (ej: "00", "ACCP", "AC00")
    - message: Descripción del resultado
    - reference: Número de referencia (opcional)
    - success: Indica si fue exitoso (opcional)
    - Id: Identificador único de la operación (opcional)
    - uuid: Identificador UUID (opcional)
    
    Códigos comunes:
    - "00": Operación exitosa
    - "ACCP": Operación aceptada
    - "AC00": Operación en espera
    - "202": Mensaje recibido satisfactoriamente
    """
    
    code: str  # Código de resultado
    message: str  # Descripción del resultado
    reference: Optional[str] = None  # Referencia (opcional)
    success: Optional[bool] = None  # Éxito (opcional)
    Id: Optional[str] = None  # ID de operación (opcional)
    uuid: Optional[str] = None  # UUID (opcional)


class SuccessResponse(BaseModel):
    """
    FORMATO PARA RESPUESTAS DE ÉXITO/ERROR SIMPLES
    
    ¿Cuándo se usa?
    - Para operaciones que solo necesitan indicar éxito/fallo
    - Para respuestas simples sin muchos detalles
    - Especialmente útil para dispersión de pagos
    
    Campos:
    - success: true si fue exitoso, false si falló
    - message: Descripción del resultado
    - error: Detalles del error si algo falló (opcional)
    """
    
    success: bool  # true = éxito, false = error
    message: str  # Descripción del resultado
    error: Optional[str] = None  # Detalles del error (opcional)


# RESUMEN DE TODOS LOS ESQUEMAS
# =============================
"""
ESQUEMAS DEFINIDOS EN ESTE ARCHIVO:

ESQUEMAS DE ENTRADA (Request):
1. IntegracionPayload - Para endpoint genérico
2. R4BcvRequest - Para consulta de tasa BCV
3. R4ConsultaRequest - Para consulta de cliente
4. R4NotificaRequest - Para notificación de pago
5. R4PagosRequest - Para dispersión de pagos
6. R4VueltoRequest - Para envío de vuelto
7. GenerarOtpRequest - Para generar OTP
8. DebitoInmediatoRequest - Para débito inmediato
9. CreditoInmediatoRequest - Para crédito inmediato
10. DomiciliacionCNTARequest - Para domiciliación por cuenta
11. DomiciliacionCELERequest - Para domiciliación por teléfono
12. ConsultarOperacionesRequest - Para consultar operaciones
13. CICuentasRequest - Para crédito con cuentas
14. R4C2PRequest - Para cobro C2P
15. R4AnulacionC2PRequest - Para anulación C2P

ESQUEMAS DE SALIDA (Response):
1. R4BcvResponse - Respuesta de tasa BCV
2. R4ConsultaResponse - Respuesta de consulta cliente
3. R4NotificaResponse - Respuesta de notificación
4. StandardResponse - Respuesta estándar genérica
5. SuccessResponse - Respuesta simple de éxito/error

ESQUEMAS AUXILIARES:
1. PersonaPago - Para beneficiarios en dispersión

TODOS los esquemas incluyen:
- Validación automática de tipos de datos
- Documentación detallada de cada campo
- Campos opcionales claramente marcados
- Descripciones en español fáciles de entender
"""