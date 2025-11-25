"""
CONTROLADORES DE LA API R4 CONECTA
==================================

Este archivo contiene todos los "puntos de entrada" de nuestra API.
Piensa en cada función como una "puerta" por donde pueden entrar las peticiones del banco.

¿Qué hace este archivo?
- Define todas las URLs que acepta nuestra API (como /MBbcv, /R4pagos, etc.)
- Recibe los datos que envía el banco
- Verifica que los datos sean correctos y seguros
- Procesa la información y devuelve una respuesta

Creado por: Alicson Rubio
Fecha: 11/2025
"""

# IMPORTACIONES - Aquí traemos las herramientas que necesitamos
# ============================================================

from fastapi import APIRouter, HTTPException, Request, Body, Depends
# FastAPI: Framework web que nos ayuda a crear la API
# APIRouter: Nos permite organizar las rutas/URLs
# HTTPException: Para manejar errores HTTP
# Request: Para acceder a la información de la petición
# Body: Para recibir datos en el cuerpo de la petición
# Depends: Para verificar autenticación y permisos

from models.schemas import *
# Importamos todos los "moldes" o esquemas que definen cómo deben verse los datos

from services import r4_client
# Cliente genérico para procesar datos de R4

from services.r4_services import R4Services
# Servicios específicos con la lógica de negocio de cada operación

from core import auth
# Módulo de autenticación y seguridad

import uuid
# Para generar identificadores únicos
import logging
from db.connector import test_connection

# CONFIGURACIÓN DEL ROUTER
# ========================
# Esto es como el "organizador" de todas nuestras rutas/URLs
router = APIRouter(prefix="", tags=["integracion"])
logger = logging.getLogger(__name__)

# ENDPOINT GENÉRICO DE INTEGRACIÓN
# ================================
# @router.post("/integrar")
# async def integrar(payload: IntegracionPayload):
#     """
#     ENDPOINT GENÉRICO PARA RECIBIR DATOS DE R4
    
#     ¿Qué hace?
#     - Recibe cualquier tipo de información del sistema R4
#     - La guarda en la base de datos usando un procedimiento almacenado
#     - Devuelve confirmación de que se procesó correctamente
    
#     ¿Cuándo se usa?
#     - Para operaciones generales que no tienen un endpoint específico
#     - Como punto de entrada principal para el flujo "bpush"
    
#     Parámetros:
#     - payload: Los datos que envía R4 (puede ser cualquier información)
    
#     Respuesta:
#     - ok: True si todo salió bien, False si hubo error
#     - resultado: Detalles del procesamiento
#     """
#     try:
#         # Intentamos procesar y guardar los datos
#         resultado = await r4_client.procesar_y_guardar(payload.dict())
        
#         # Si todo salió bien, devolvemos confirmación
#         return {"ok": True, "resultado": resultado}
        
#     except Exception as e:
#         # Si algo salió mal, devolvemos un error
#         # En producción esto debería ir a los logs del sistema
#         raise HTTPException(status_code=500, detail=str(e))


# CONSULTA DE TASA DEL BANCO CENTRAL DE VENEZUELA (BCV)
# =====================================================
@router.post("/MBbcv", response_model=R4BcvResponse, summary="Consulta tasa BCV")
async def mbcv(payload: R4BcvRequest = Body(...), _auth=Depends(auth.verify_hmac_bcv), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    CONSULTA LA TASA DE CAMBIO OFICIAL DEL BCV
    
    ¿Qué hace?
    - Consulta la tasa de cambio oficial del dólar según el BCV
    - Verifica que la petición sea auténtica usando HMAC-SHA256
    - Devuelve la tasa de cambio para la fecha solicitada
    
    ¿Cuándo se usa?
    - Cuando necesitamos saber el valor oficial del dólar
    - Para cálculos de conversión de moneda
    
    Seguridad:
    - Requiere autenticación HMAC con la fórmula: fechavalor + moneda
    - Solo acepta peticiones con headers válidos
    
    Parámetros de entrada:
    - Moneda: Código de la moneda (ej: "USD")
    - Fechavalor: Fecha para consultar la tasa (formato: "2024-01-15")
    
    Respuesta:
    - code: "00" si fue exitoso, otro código si hubo error
    - fechavalor: La fecha consultada
    - tipocambio: El valor de la tasa (ej: 36.5314)
    """
    try:
                # Procesamos la consulta usando nuestro servicio especializado
        resultado = await R4Services.procesar_consulta_bcv(payload.Moneda, payload.Fechavalor)
        
        # Devolvemos la respuesta en el formato esperado
        return R4BcvResponse(**resultado)
        
    except Exception as e:
        # Si hay error, lo reportamos
        raise HTTPException(status_code=500, detail=str(e))


# CONSULTA Y VALIDACIÓN DE CLIENTE
# ================================
@router.post("/R4consulta", response_model=R4ConsultaResponse, summary="Consulta de cliente")
async def r4consulta(payload: R4ConsultaRequest = Body(...), _auth=Depends(auth.verify_hmac_consulta), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    VALIDA SI UN CLIENTE EXISTE Y PUEDE RECIBIR PAGOS
    En esta operacion se asume que es unas INTENCION de pago movil 
    en nuestra logica siempre respondemos si (True) a cualuquier inteincion de pago movil.
    
    ¿Qué hace?
    - Verifica si un cliente está registrado en nuestro sistema
    - Devuelve true/false según el resultado de la validación
    
    ¿Cuándo se usa?
    - Antes de procesar un pago móvil
    - Para verificar que el destinatario es válido
    - Como paso previo a la notificación de pago
    
    Proceso:
    1. El banco nos pregunra si estamos espernad un pago de x cliente
    2. Nosotros por defecto aceptamos todas las inteinciones de pago
    3. Respondemos true (sí puede) 
    4. El banco procede con el pago
    
    Parámetros de entrada:
    - IdCliente: Cédula o identificación del cliente (obligatorio)
    - Monto: Cantidad de dinero a recibir (opcional)
    - TelefonoComercio: Teléfono de nuestro comercio (opcional)
    
    Respuesta:
    - status: true si aceptamos la intencion de pago, false si no
    """
    try:
        # Procesamos la consulta del cliente
        resultado = await R4Services.procesar_consulta_cliente(
            payload.IdCliente, 
            payload.Monto, 
            payload.TelefonoComercio
        )
        
        # Devolvemos la respuesta
        return R4ConsultaResponse(**resultado)
        
    except Exception as e:
        # Si hay error, lo reportamos
        raise HTTPException(status_code=500, detail=str(e))


# NOTIFICACIÓN DE PAGO MÓVIL RECIBIDO
# ===================================
@router.post("/R4notifica", response_model=R4NotificaResponse, summary="Notificación de pago (Pago móvil)")
async def r4notifica(payload: R4NotificaRequest = Body(...), _auth=Depends(auth.verify_hmac_notifica), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    RECIBE NOTIFICACIÓN DE QUE NOS LLEGÓ UN PAGO MÓVIL
    
    ¿Qué hace?
    - El banco nos notifica que alguien nos envió un pago móvil
    - Guardamos toda la información del pago en nuestra base de datos
    - Retornamos True/False si el proceso fue exitoso o no
    
    ¿Cuándo se usa?
    - Cuando alguien nos envía un pago móvil desde su banco
    - Es la confirmación oficial de que el dinero llegó
    
    Proceso completo:
    0. Pasa por la consulta de intencion de pago (R4consulta)
    1. Cliente hace pago móvil a nuestra cuenta
    2. El banco R4 nos notifica a nosotros (aquí)
    3. Nosotros decidimos si aceptar o rechazar (según validaciones internas)
    4. Si todo el registro no existe lo aceptamos y retornamos abono=True, si existe un rechazo por banco o por nosotros retornamos abono=False
    
    Parámetros de entrada:
    - IdComercio: Nuestra cédula/RIF como comercio
    - TelefonoComercio: Nuestro teléfono registrado
    - TelefonoEmisor: Teléfono de quien nos envió el pago
    - Concepto: Descripción del pago (ej: "Compra de producto")
    - BancoEmisor: Código del banco de quien envía
    - Monto: Cantidad de dinero recibida
    - FechaHora: Cuándo se hizo el pago
    - Referencia: Número único de la transacción
    - CodigoRed: Código que indica si el pago fue exitoso
    
    Respuesta:
    - abono: true si no hubo errores, false si hubo algún problema
    """
    try:
    #     # Procesamos la notificación del pago
        resultado = await R4Services.procesar_notificacion_pago(payload.dict())
        
        # Devolvemos si aceptamos o no el abono
        #print(resultado)
        if  resultado.get('abono') is None: 
            raise HTTPException(status_code=500, detail=f"Error interno: respuesta inválida del servicio {resultado.get('mensaje')}")
        # if resultado.get('abono') == False: 
        #     #raise HTTPException(status_code=409, detail=f"Notificación rechazada: {resultado.get('mensaje')}")
        #     print("Notificación rechazada: ", resultado.get('mensaje'))            
        return R4NotificaResponse(**resultado)
        
    except Exception as e:
        # Si hay error, lo reportamos
        raise HTTPException(status_code=500, detail=str(e))

     # Validación básica de estructura
    #     if not isinstance(resultado, dict):
    #         raise HTTPException(status_code=500, detail="Respuesta inválida del servicio R4")

    #     # Normalizar posibles claves
    #     codigo =  resultado.get("p_codigo")
    #     mensaje = resultado.get("p_mensaje")
    #     abono = resultado
    #     success_flag = resultado.get("success") if "success" in resultado else None
    #     print (resultado,codigo, mensaje, abono, success_flag)

    #     # Si hay código explícito del SP lo priorizamos
    #     if codigo is not None:
    #         try:
    #             codigo_int = int(codigo)
    #         except Exception:
    #             codigo_int = None

    #         # Log para trazabilidad
    #         import logging
    #         logger = logging.getLogger("r4conecta.endpoints")
    #         logger.info(f"R4notifica -> SP codigo={codigo_int} mensaje={mensaje}")

    #         if codigo_int == 1:
    #             # Éxito
    #             return R4NotificaResponse(abono=True, resultado=resultado)
    #         elif codigo_int == 0:
    #             # Duplicado / ya procesada
    #             return R4NotificaResponse(abono=False, mensaje=resultado)
    #         else:
    #             # Cualquier otro código del SP se considera error
    #             raise HTTPException(status_code=500, detail=f"Error procesando notificación (SP code={codigo_int}): {mensaje}")

    #     # Si no hay código, usar flags alternativos
    #     if success_flag is not None:
    #         if success_flag:
    #             # Si viene abono explícito lo respetamos, sino consideramos éxito
    #             if abono is not None:
    #                 return R4NotificaResponse(abono=bool(abono), mensaje=mensaje)
    #             return R4NotificaResponse(abono=True, mensaje=mensaje)
    #         else:
    #             raise HTTPException(status_code=500, detail=mensaje or "Error en servicio R4")

    #     if abono is not None:
    #         if abono:
    #             return R4NotificaResponse(abono=True, mensaje=mensaje)
    #         # Si abono == False sin código, tratar como rechazo -> 500 para no indicar "ok"
    #         raise HTTPException(status_code=500, detail=mensaje or "Notificación rechazada respuesta 'None'")

    #     # Fallback: respuesta no interpretable
    #     raise HTTPException(status_code=500, detail="Respuesta no interpretable del servicio R4")

    # except HTTPException:
    #     # Propagar HTTPException tal cual (ya registra el status adecuado)
    #     raise
    # except Exception as e:
    #     # Log del error y devolver 500
    #     import logging
    #     logger = logging.getLogger("r4conecta.endpoints")
    #     logger.exception("Error procesando R4notifica")
    #     raise HTTPException(status_code=500, detail=str(e))


# GESTIÓN DE PAGOS MÚLTIPLES (DISPERSIÓN)
# =======================================
@router.post("/R4pagos", response_model=SuccessResponse, summary="Gestión de Pagos (dispersión)")
async def r4pagos(payload: R4PagosRequest = Body(...), _auth=Depends(auth.verify_hmac_pagos), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    ENVÍA DINERO A MÚLTIPLES PERSONAS DE UNA SOLA VEZ
    
    ¿Qué hace?
    - Toma un monto total y lo reparte entre varias personas
    - Envía pagos móviles a múltiples beneficiarios simultáneamente
    - Es como hacer varios pagos móviles al mismo tiempo
    
    ¿Cuándo se usa?
    - Para pagar nóminas (salarios a empleados)
    - Para repartir ganancias entre socios
    - Para hacer pagos masivos a proveedores
    
    Ejemplo práctico:
    - Tenemos 1000 Bs para repartir
    - Queremos enviar 400 Bs a Juan y 600 Bs a María
    - Este endpoint hace ambos pagos automáticamente
    
    Seguridad:
    - Requiere autenticación HMAC con: monto + fecha
    - Verifica que la suma de pagos parciales = monto total
    
    Parámetros de entrada:
    - monto: Cantidad total a dispersar (ej: "1000.00")
    - fecha: Fecha del pago en formato MM/DD/YYYY
    - Referencia: Número de referencia único
    - personas: Lista de beneficiarios, cada uno con:
      * nombres: Nombre completo del beneficiario
      * documento: Cédula con tipo (ej: "V12345678")
      * destino: Número de cuenta bancaria (20 dígitos)
      * montoPart: Cantidad que le corresponde
    
    Respuesta:
    - success: true si todos los pagos fueron exitosos
    - message: Descripción del resultado
    - error: Detalles del error si algo falló
    """
    # Procesamos la dispersión de pagos
    resultado = await R4Services.procesar_gestion_pagos(payload.dict())
    
    # Devolvemos el resultado
    return SuccessResponse(**resultado)


# PROCESAMIENTO DE VUELTO
# =======================
@router.post("/MBvuelto", response_model=StandardResponse, summary="R4 Vuelto")
async def mb_vuelto(payload: R4VueltoRequest = Body(...), _auth=Depends(auth.verify_hmac_vuelto), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    ENVÍA DINERO DE VUELTA A UN CLIENTE (VUELTO)
    
    ¿Qué hace?
    - Devuelve dinero a un cliente mediante pago móvil
    - Es como dar "vuelto" en una transacción
    - Procesa el pago y devuelve una referencia única
    
    ¿Cuándo se usa?
    - Cuando un cliente pagó de más y hay que devolverle
    - Para reembolsos por productos devueltos
    - Para correcciones de pagos incorrectos
    
    Ejemplo:
    - Cliente pagó 100 Bs por un producto de 80 Bs
    - Le devolvemos 20 Bs usando este endpoint
    
    Seguridad:
    - Requiere HMAC con: TelefonoDestino + Monto + Banco + Cedula
    
    Parámetros de entrada:
    - TelefonoDestino: Teléfono del cliente que recibirá el vuelto
    - Cedula: Cédula del cliente (con tipo: V, E, J, P)
    - Banco: Código del banco del cliente (4 dígitos)
    - Monto: Cantidad a devolver
    - Concepto: Descripción del vuelto (opcional)
    - Ip: Dirección IP desde donde se hace la operación (opcional)
    
    Respuesta:
    - code: "00" si fue exitoso, otro código si hubo error
    - message: Descripción del resultado
    - reference: Número de referencia único del pago
    """
    try:
        # Guardamos la información del vuelto
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos una referencia única para el pago
        # uuid4() crea un identificador único, tomamos solo 8 dígitos
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="00", 
            message="TRANSACCION EXITOSA", 
            reference=reference
        )
        
    except Exception as e:
        # Si hay error, devolvemos código de token inválido
        return StandardResponse(code="08", message="Token Inválido")


# GENERACIÓN DE CÓDIGO OTP (One Time Password)
# ============================================
@router.post("/GenerarOtp", response_model=StandardResponse, summary="Generar OTP")
async def generar_otp(payload: GenerarOtpRequest = Body(...), _auth=Depends(auth.verify_hmac_generar_otp), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    SOLICITA LA GENERACIÓN DE UN CÓDIGO OTP TEMPORAL
    
    ¿Qué es un OTP?
    - OTP = One Time Password (Contraseña de Un Solo Uso)
    - Es un código numérico temporal (ej: 123456)
    - Se envía por SMS al cliente para confirmar operaciones
    - Solo sirve una vez y por tiempo limitado
    
    ¿Qué hace este endpoint?
    - Le pide al banco del cliente que genere un OTP
    - El banco envía el código por SMS al cliente
    - El cliente usa ese código para confirmar la operación
    
    ¿Cuándo se usa?
    - Antes de hacer un débito inmediato
    - Para operaciones que requieren confirmación del cliente
    - Como medida de seguridad adicional
    
    Proceso completo:
    1. Nosotros llamamos este endpoint
    2. El banco genera un código (ej: 789123)
    3. El banco envía SMS al cliente: "Su código es: 789123"
    4. El cliente nos dice el código
    5. Usamos ese código en el siguiente paso (débito)
    
    Seguridad:
    - Requiere HMAC con: Banco + Monto + Telefono + Cedula
    
    Parámetros de entrada:
    - Banco: Código del banco del cliente (4 dígitos)
    - Monto: Cantidad que se va a debitar
    - Telefono: Teléfono donde se enviará el SMS
    - Cedula: Cédula del cliente (con tipo: V, E, J, P)
    
    Respuesta:
    - code: "202" si se procesó correctamente
    - message: Confirmación de que se envió la solicitud
    - success: true si todo salió bien
    """
    try:
        # Guardamos la solicitud de OTP
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Devolvemos confirmación de que se procesó
        return StandardResponse(
            code="202", 
            message="Se ha recibido el mensaje de forma satisfactoria", 
            success=True
        )
        
    except Exception as e:
        # Si hay error, lo reportamos
        raise HTTPException(status_code=500, detail=str(e))


# DÉBITO INMEDIATO (COBRAR DINERO AL CLIENTE)
# ===========================================
@router.post("/DebitoInmediato", response_model=StandardResponse, summary="Débito Inmediato")
async def debito_inmediato(payload: DebitoInmediatoRequest = Body(...), _auth=Depends(auth.verify_hmac_debito_inmediato), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    COBRA DINERO DIRECTAMENTE DE LA CUENTA DEL CLIENTE
    
    ¿Qué hace?
    - Descuenta dinero de la cuenta bancaria del cliente
    - Es como hacer un cargo automático
    - Requiere confirmación previa del cliente (OTP)
    
    ¿Cuándo se usa?
    - Para cobrar servicios automáticamente
    - Para domiciliaciones bancarias
    - Para pagos recurrentes (mensualidades, etc.)
    
    Proceso completo:
    1. Primero se genera un OTP (paso anterior)
    2. El cliente recibe el código por SMS
    3. El cliente nos autoriza con el código
    4. Nosotros ejecutamos este débito con el OTP
    5. El dinero se descuenta de su cuenta
    
    IMPORTANTE:
    - Solo funciona si el cliente ya autorizó con OTP
    - Es una operación irreversible
    - Requiere máxima seguridad
    
    Seguridad:
    - Requiere HMAC con: Banco + Cedula + Telefono + Monto + OTP
    
    Parámetros de entrada:
    - Banco: Código del banco del cliente
    - Monto: Cantidad a debitar
    - Telefono: Teléfono del cliente
    - Cedula: Cédula del cliente
    - Nombre: Nombre completo del cliente
    - OTP: Código que recibió el cliente por SMS
    - Concepto: Descripción del cobro
    
    Respuestas posibles:
    - ACCP: Operación aceptada inmediatamente
    - AC00: Operación en espera (hay que consultar después)
    - Otros códigos: Error en la operación
    """
    try:
        # Guardamos la información del débito
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos identificadores únicos
        operation_id = str(uuid.uuid4())  # ID único de la operación
        reference = str(uuid.uuid4().int)[:8]  # Referencia numérica
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="ACCP", 
            message="Operación Aceptada", 
            reference=reference, 
            Id=operation_id
        )
        
    except Exception as e:
        # Si hay error, la operación queda en espera
        operation_id = str(uuid.uuid4())
        return StandardResponse(
            code="AC00", 
            message="Operación en Espera de Respuesta del Receptor", 
            Id=operation_id
        )


# CRÉDITO INMEDIATO (ENVIAR DINERO AL CLIENTE)
# ============================================
@router.post("/CreditoInmediato", response_model=StandardResponse, summary="Crédito Inmediato")
async def credito_inmediato(payload: CreditoInmediatoRequest = Body(...), _auth=Depends(auth.verify_hmac_credito_inmediato), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    ENVÍA DINERO DIRECTAMENTE A LA CUENTA DEL CLIENTE
    
    ¿Qué hace?
    - Deposita dinero en la cuenta bancaria del cliente
    - Es como hacer una transferencia instantánea
    - El dinero llega inmediatamente a su cuenta
    
    ¿Cuándo se usa?
    - Para pagar a proveedores
    - Para enviar reembolsos
    - Para transferir ganancias
    - Para pagos de nómina individual
    
    Diferencia con pago móvil:
    - Pago móvil: Se envía al teléfono, el cliente debe aceptar
    - Crédito inmediato: Se deposita directo en la cuenta
    
    Seguridad:
    - Requiere HMAC con: Banco + Cedula + Telefono + Monto
    
    Parámetros de entrada:
    - Banco: Código del banco del beneficiario
    - Cedula: Cédula del beneficiario
    - Telefono: Teléfono del beneficiario
    - Monto: Cantidad a enviar
    - Concepto: Descripción del pago
    
    Respuestas posibles:
    - ACCP: Dinero enviado exitosamente
    - AC00: Operación en proceso (consultar después)
    - Otros: Error en la operación
    """
    try:
        # Guardamos la información del crédito
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos identificadores únicos
        operation_id = str(uuid.uuid4())
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="ACCP", 
            message="Operación Aceptada", 
            reference=reference, 
            Id=operation_id
        )
        
    except Exception as e:
        # Si hay error, la operación queda en espera
        operation_id = str(uuid.uuid4())
        return StandardResponse(
            code="AC00", 
            message="Operación en Espera de Respuesta del Receptor", 
            Id=operation_id
        )


# DOMICILIACIÓN POR NÚMERO DE CUENTA
# ==================================
@router.post("/TransferenciaOnline/DomiciliacionCNTA", response_model=StandardResponse, summary="Domiciliación de cuentas 20 dígitos")
async def domiciliacion_cnta(payload: DomiciliacionCNTARequest = Body(...), _auth=Depends(auth.verify_hmac_domiciliacion_cnta), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    CONFIGURA COBRO AUTOMÁTICO USANDO NÚMERO DE CUENTA
    
    ¿Qué es domiciliación?
    - Es autorizar cobros automáticos recurrentes
    - Como cuando el banco te cobra la mensualidad de la tarjeta
    - El cliente autoriza una vez, nosotros cobramos cuando queramos
    
    ¿Qué hace este endpoint?
    - Registra una cuenta bancaria para cobros automáticos
    - Usa el número de cuenta completo (20 dígitos)
    - Configura el monto y concepto del cobro
    
    ¿Cuándo se usa?
    - Para servicios de suscripción mensual
    - Para seguros con pago automático
    - Para servicios públicos (luz, agua, etc.)
    - Para préstamos con cuotas automáticas
    
    Proceso:
    1. Cliente nos autoriza cobrar de su cuenta
    2. Registramos su cuenta con este endpoint
    3. Cada mes cobramos automáticamente
    4. No necesita aprobar cada cobro individual
    
    Seguridad:
    - Requiere HMAC con: cuenta (número completo)
    - Solo funciona con cuentas válidas y activas
    
    Parámetros de entrada:
    - docId: Cédula del titular de la cuenta
    - nombre: Nombre completo del titular
    - cuenta: Número de cuenta bancaria (20 dígitos)
    - monto: Cantidad autorizada a cobrar
    - concepto: Descripción del servicio a cobrar
    
    Respuesta:
    - codigo: "202" si se registró correctamente
    - mensaje: Confirmación del registro
    - uuid: Identificador único de la domiciliación
    """
    try:
        # Guardamos la información de domiciliación
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos identificador único para esta domiciliación
        operation_uuid = str(uuid.uuid4())
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="202", 
            message="Se ha recibido el mensaje de forma satisfactoria", 
            uuid=operation_uuid
        )
        
    except Exception as e:
        # Si hay error en los datos
        return StandardResponse(
            code="07", 
            message="Request Inválida, error en el campo: DocId", 
            uuid=""
        )


# DOMICILIACIÓN POR TELÉFONO
# =========================
@router.post("/TransferenciaOnline/DomiciliacionCELE", response_model=StandardResponse, summary="Domiciliación por teléfono")
async def domiciliacion_cele(payload: DomiciliacionCELERequest = Body(...), _auth=Depends(auth.verify_hmac_domiciliacion_cele), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    CONFIGURA COBRO AUTOMÁTICO USANDO TELÉFONO
    
    ¿Qué hace?
    - Similar a la domiciliación por cuenta
    - Pero usa el teléfono en lugar del número de cuenta
    - Más fácil para el cliente (solo necesita su teléfono)
    
    ¿Cuándo se usa?
    - Cuando el cliente no sabe su número de cuenta
    - Para servicios más simples y accesibles
    - Para clientes que prefieren usar pago móvil
    
    NOTA IMPORTANTE:
    - El primer envío es solo para afiliación
    - No genera cobro inmediato
    - El cliente debe confirmar en su banco primero
    
    Proceso:
    1. Enviamos solicitud de afiliación
    2. Cliente va a su banco y autoriza
    3. Una vez autorizado, podemos cobrar automáticamente
    
    Seguridad:
    - Requiere HMAC con: telefono
    
    Parámetros de entrada:
    - docId: Cédula del cliente
    - telefono: Teléfono registrado en pago móvil
    - nombre: Nombre completo del cliente
    - banco: Código del banco del cliente
    - monto: Cantidad autorizada a cobrar
    - concepto: Descripción del servicio
    
    Respuesta:
    - codigo: "202" si se procesó correctamente
    - mensaje: Confirmación del procesamiento
    - uuid: Identificador único de la solicitud
    """
    try:
        # Guardamos la información de domiciliación por teléfono
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos identificador único
        operation_uuid = str(uuid.uuid4())
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="202", 
            message="Se ha recibido el mensaje de forma satisfactoria", 
            uuid=operation_uuid
        )
        
    except Exception as e:
        # Si hay error en los datos
        return StandardResponse(
            code="07", 
            message="Request Inválida, error en el campo: DocId", 
            uuid=""
        )


# CONSULTA DE ESTADO DE OPERACIONES
# =================================
@router.post("/ConsultarOperaciones", response_model=StandardResponse, summary="Consultar Operaciones")
async def consultar_operaciones(payload: ConsultarOperacionesRequest = Body(...), _auth=Depends(auth.verify_hmac_consultar_operaciones), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    CONSULTA EL ESTADO ACTUAL DE UNA OPERACIÓN
    
    ¿Qué hace?
    - Verifica si una operación anterior ya se completó
    - Obtiene el resultado final de operaciones en espera
    - Es como "preguntar" si ya se procesó algo
    
    ¿Cuándo se usa?
    - Cuando una operación respondió "AC00" (en espera)
    - Para verificar débitos o créditos pendientes
    - Para confirmar si un pago ya se procesó
    
    ¿Por qué es necesario?
    - Algunas operaciones no son instantáneas
    - Los bancos pueden tardar en procesar
    - Necesitamos saber cuándo ya terminaron
    
    Ejemplo de uso:
    1. Hacemos un débito inmediato
    2. Responde "AC00" (en espera)
    3. Esperamos unos minutos
    4. Consultamos con este endpoint
    5. Ahora responde "ACCP" (completado)
    
    Seguridad:
    - Requiere HMAC con: Id (identificador de la operación)
    
    Parámetros de entrada:
    - Id: Identificador único de la operación a consultar
           (es el UUID que devolvió la operación original)
    
    Respuesta:
    - code: Estado actual ("ACCP" = completado, otros = pendiente/error)
    - reference: Número de referencia si se completó
    - success: true si la consulta fue exitosa
    """
    try:
        # Simulamos consulta exitosa (en producción consultaría la BD real)
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos estado completado
        return StandardResponse(
            code="ACCP", 
            reference=reference, 
            success=True
        )
        
    except Exception as e:
        # Si hay error en la consulta
        raise HTTPException(status_code=500, detail=str(e))


# CRÉDITO INMEDIATO CON CUENTA DE 20 DÍGITOS
# ==========================================
@router.post("/CICuentas", response_model=StandardResponse, summary="Crédito Inmediato cuentas 20 dígitos")
async def ci_cuentas(payload: CICuentasRequest = Body(...), _auth=Depends(auth.verify_hmac_ci_cuentas), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    ENVÍA DINERO USANDO EL NÚMERO DE CUENTA COMPLETO
    
    ¿Qué hace?
    - Similar al crédito inmediato normal
    - Pero usa el número de cuenta en lugar del teléfono
    - Más preciso y directo
    
    ¿Cuándo se usa?
    - Para transferencias empresariales
    - Cuando necesitamos máxima precisión
    - Para cuentas que no tienen pago móvil activo
    
    Ventajas:
    - No depende del pago móvil
    - Más rápido (va directo a la cuenta)
    - Menos posibilidad de error
    
    Seguridad:
    - Requiere HMAC con: Cedula + Cuenta + Monto
    - Verifica que la cuenta sea válida
    
    Parámetros de entrada:
    - Cedula: Cédula del beneficiario
    - Cuenta: Número de cuenta completo (20 dígitos)
    - Monto: Cantidad a enviar
    - Concepto: Descripción del pago
    
    Respuesta:
    - code: "ACCP" si fue exitoso
    - message: Descripción del resultado
    - reference: Número de referencia único
    """
    try:
        # Guardamos la información del crédito
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos referencia única
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="ACCP", 
            message="Operación Aceptada", 
            reference=reference
        )
        
    except Exception as e:
        # Si hay error, la operación queda en espera
        operation_id = str(uuid.uuid4())
        return StandardResponse(
            code="AC00", 
            message="Operación en Espera de Respuesta del Receptor", 
            Id=operation_id
        )


# COBRO C2P (Cliente a Persona)
# =============================
@router.post("/MBc2p", response_model=StandardResponse, summary="Cobro C2P")
async def mb_c2p(payload: R4C2PRequest = Body(...), _auth=Depends(auth.verify_hmac_c2p), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    PROCESA COBRO DIRECTO AL CLIENTE (C2P = Client to Person)
    
    ¿Qué es C2P?
    - C2P = Client to Person (Cliente a Persona)
    - Es cuando nosotros le cobramos directamente al cliente
    - Similar al débito, pero con proceso diferente
    
    ¿Qué hace?
    - Cobra dinero directamente del cliente
    - Requiere código OTP del cliente
    - Procesa el pago inmediatamente
    
    ¿Cuándo se usa?
    - Para cobros en punto de venta
    - Para servicios que requieren pago inmediato
    - Como alternativa al débito inmediato
    
    Proceso:
    1. Cliente autoriza el cobro con su OTP
    2. Nosotros ejecutamos este endpoint
    3. El dinero se descuenta de su cuenta
    4. Recibimos confirmación inmediata
    
    Seguridad:
    - Requiere HMAC con: TelefonoDestino + Monto + Banco + Cedula
    - Requiere OTP válido del cliente
    
    Parámetros de entrada:
    - TelefonoDestino: Teléfono del cliente
    - Cedula: Cédula del cliente
    - Concepto: Descripción del cobro
    - Banco: Código del banco del cliente
    - Ip: Dirección IP desde donde se hace
    - Monto: Cantidad a cobrar
    - Otp: Código de autorización del cliente
    
    Respuesta:
    - code: "00" si fue exitoso
    - message: Descripción del resultado
    - reference: Número de referencia único
    """
    try:
        # Guardamos la información del cobro C2P
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos referencia única
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="00", 
            message="TRANSACCION EXITOSA", 
            reference=reference
        )
        
    except Exception as e:
        # Si hay error, devolvemos token inválido
        return StandardResponse(code="08", message="TOKEN inválido")


# ANULACIÓN DE COBRO C2P
# ======================
@router.post("/MBanulacionC2P", response_model=StandardResponse, summary="Anulación C2P")
async def mb_anulacion_c2p(payload: R4AnulacionC2PRequest = Body(...), _auth=Depends(auth.verify_hmac_anulacion_c2p), _ip=Depends(auth.ip_whitelist_middleware)):
    """
    CANCELA UN COBRO C2P PREVIAMENTE REALIZADO
    
    ¿Qué hace?
    - Anula (cancela) un cobro C2P que ya se hizo
    - Devuelve el dinero al cliente
    - Es como un "reverso" de la operación
    
    ¿Cuándo se usa?
    - Cuando hubo un error en el cobro
    - Para cancelar transacciones duplicadas
    - Cuando el cliente solicita anulación
    - Para corregir montos incorrectos
    
    IMPORTANTE:
    - Solo se pueden anular operaciones recientes
    - Debe tener la referencia exacta del cobro original
    - Es una operación irreversible
    
    Proceso:
    1. Identificamos el cobro a anular por su referencia
    2. Verificamos que sea anulable
    3. Procesamos la devolución
    4. El dinero regresa al cliente
    
    Seguridad:
    - Requiere HMAC con: Banco
    - Verifica que la operación original exista
    
    Parámetros de entrada:
    - Cedula: Cédula del cliente original
    - Banco: Código del banco del cliente
    - Referencia: Número de referencia del cobro a anular
    
    Respuesta:
    - code: "00" si la anulación fue exitosa
    - message: Confirmación de la anulación
    - reference: Nueva referencia de la anulación
    """
    try:
        # Guardamos la información de la anulación
        resultado = await r4_client.procesar_y_guardar(payload.dict())
        
        # Generamos nueva referencia para la anulación
        reference = str(uuid.uuid4().int)[:8]
        
        # Devolvemos confirmación exitosa
        return StandardResponse(
            code="00", 
            message="TRANSACCION EXITOSA", 
            reference=reference
        )
        
    except Exception as e:
        # Si hay error, el servicio no está activo
        return StandardResponse(
            code="41", 
            message="Servicio no activo o negada por el banco"
        )


# ENDPOINTS DE SISTEMA
# ====================
@router.get("/health")
async def health_check():
    from datetime import datetime
    """Verificar estado de la API"""
    try:        
        db_ok = await test_connection()
        status = "ok" if db_ok else "degraded"
        if not db_ok:
            logger.error("Fallo en verificación de conexión a BD (SELECT 1)")
        
        return {
            "status": status,
            "message": "API R4 Conecta funcionando correctamente",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "endpoints_count": len(router.routes),
            "Conectado": db_ok
        }
    except Exception as err:
        logger.exception(f"Error en health_check: {err}")
        raise HTTPException(status_code=500, detail="Health check interno falló")
        #raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def root():
    """Información básica de la API"""
    return {
        "name": "API R4 Conecta",
        "version": "3.0",
        "endpoints": [
            "/integrar", "/MBbcv", "/R4consulta", "/R4notifica", "/R4pagos",
            "/MBvuelto", "/GenerarOtp", "/DebitoInmediato", "/CreditoInmediato",
            "/TransferenciaOnline/DomiciliacionCNTA", "/TransferenciaOnline/DomiciliacionCELE",
            "/ConsultarOperaciones", "/CICuentas", "/MBc2p", "/MBanulacionC2P"
        ]
    }