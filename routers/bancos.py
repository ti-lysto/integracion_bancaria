"""ROUTER PRINCIPAL MULTI-BANCO - EXPLICACIÓN PARA NO PROGRAMADORES
=====================================================================

¿QUÉ HACE ESTE ARCHIVO?
-----------------------
Este archivo es como un RECEPCIONISTA que recibe todas las peticiones
de los bancos y las dirige al banco correcto.

Piensa en esto como un HOTEL con 24 habitaciones (una por cada banco):
- Cuando llega un huésped (petición del banco), el recepcionista mira
  el número de habitación (código del banco) y lo dirige correctamente.
- Cada habitación tiene su propio servicio personalizado.

¿CÓMO FUNCIONA?
--------------
1. Un banco envía una petición a: /api/0134/MBbcv
2. Este archivo ve que 0134 = Banesco
3. Busca el servicio de Banesco
4. Le pasa la información al servicio de Banesco
5. Banesco procesa y devuelve la respuesta
6. Este archivo devuelve la respuesta al banco original

RUTAS DISPONIBLES:
-----------------
- /api/{banco}/MBbcv          → Consultar tasa de cambio
- /api/{banco}/R4consulta     → Verificar si un cliente existe
- /api/{banco}/R4notifica     → Recibir notificación de pago

EJEMPLOS DE USO:
---------------
- /api/0134/MBbcv     → Banesco consulta tasa
- /api/banesco/MBbcv  → Mismo banco, diferente forma de acceso
- /api/0102/MBbcv     → BDV consulta tasa
- /api/bdv/MBbcv      → Mismo banco BDV, por alias

VARIABLES IMPORTANTES:
---------------------
- nombre_banco: El código o alias del banco (ej: 0134 o banesco)
- payload: La información que envía el banco (datos del pago, cliente, etc.)
- servicio: El programa específico que maneja cada banco

FLUJO DE INFORMACIÓN:
--------------------
BANCO → ESTE ARCHIVO → SERVICIO DEL BANCO → BASE DE DATOS → RESPUESTA → BANCO

Creado por: Alicson Rubio
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict
from services.bancos.r4_service import R4Service
from services.bancos.base_service import BaseBankService
from services.bancos.r4_servicio import BankServiceFactory, BankR4Adapter
from models.schemas import IntegracionPayload
from models.schemas import (
    R4BcvRequest, R4ConsultaRequest, R4NotificaRequest,
    R4PagosRequest, R4VueltoRequest, GenerarOtpRequest,
    DebitoInmediatoRequest, CreditoInmediatoRequest,
    DomiciliacionCNTARequest, DomiciliacionCELERequest,
    ConsultarOperacionesRequest, CICuentasRequest,
    R4C2PRequest, R4AnulacionC2PRequest,
    StandardResponse, SuccessResponse, VerificoPagoRequest
)

router = APIRouter(prefix="/api")


# Mapeo de bancos (códigos y alias) al servicio. Por ahora todos usan el mismo
# modelo/servicio de R4. Esto permite probar integraciones multi-banco sin
# alterar la lógica específica de R4.
from core.bank_registry import (
    get_service_for_bank as registry_get_service,
    obtener_servicio_para_banco,
    obtener_config_banco,
)


def get_service_for_bank(banco: str) -> BaseBankService:
    """Resolver el servicio por código o alias.

    Acepta tanto nombres ('r4' o 'banesco') como códigos ('0102'). Normaliza
    la entrada y devuelve la instancia del servicio correspondiente.
    """
    if not banco:
        raise HTTPException(status_code=400, detail="Parámetro 'banco' requerido")

    try:
        return registry_get_service(banco)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Servicio para banco '{banco}' no disponible: {e}")



@router.post("/{nombre_banco}/MBbcv")
async def mbbcv(nombre_banco: str, payload: R4BcvRequest):
    """Endpoint que replica el comportamiento MBbcv por banco."""
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.consultar_tasa(payload.dict())


@router.post("/{nombre_banco}/R4consulta")
async def r4consulta(nombre_banco: str, payload: R4ConsultaRequest):
    """Endpoint que replica la consulta de cliente por banco (R4)."""
    servicio = get_service_for_bank(nombre_banco)
    # el adaptador implementa consulta_cliente delegando a R4Services
    return await servicio.consulta_cliente(payload.dict())
    #servicio.consulta_cliente(payload.dict())


@router.post("/{nombre_banco}/R4notifica")
async def r4notifica(nombre_banco: str, payload: R4NotificaRequest):
    """Endpoint que replica la notificación de pago por banco (R4)."""
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.procesar_notificacion(payload.dict())


@router.post("/{nombre_banco}/consulta-tasa")
async def consulta_tasa(nombre_banco: str, payload: IntegracionPayload):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.consultar_tasa(payload.dict())


@router.post("/{nombre_banco}/notificar-pago")
async def notificar_pago(nombre_banco: str, payload: IntegracionPayload, request: Request):
    servicio = get_service_for_bank(nombre_banco)
    # podrías validar headers/auth aquí o a través de dependencias
    return await servicio.procesar_notificacion(payload.dict())


@router.post("/{nombre_banco}/R4pagos")
async def r4pagos(nombre_banco: str, payload: R4PagosRequest):
    servicio = get_service_for_bank(nombre_banco)
    
    return await servicio.procesar_gestion_pagos(payload.dict())


@router.post("/{nombre_banco}/MBvuelto")
async def mb_vuelto(nombre_banco: str, payload: R4VueltoRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.procesar_vuelto(payload.dict())


@router.post("/{nombre_banco}/GenerarOtp")
async def generar_otp(nombre_banco: str, payload: GenerarOtpRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.generar_otp(payload.dict())


@router.post("/{nombre_banco}/DebitoInmediato")
async def debito_inmediato(nombre_banco: str, payload: DebitoInmediatoRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.debito_inmediato(payload.dict())


@router.post("/{nombre_banco}/CreditoInmediato")
async def credito_inmediato(nombre_banco: str, payload: CreditoInmediatoRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.credito_inmediato(payload.dict())


@router.post("/{nombre_banco}/TransferenciaOnline/DomiciliacionCNTA")
async def domiciliacion_cnta(nombre_banco: str, payload: DomiciliacionCNTARequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.domiciliacion_cnta(payload.dict())


@router.post("/{nombre_banco}/TransferenciaOnline/DomiciliacionCELE")
async def domiciliacion_cele(nombre_banco: str, payload: DomiciliacionCELERequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.domiciliacion_cele(payload.dict())


@router.post("/{nombre_banco}/ConsultarOperaciones")
async def consultar_operaciones(nombre_banco: str, payload: ConsultarOperacionesRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.consultar_operaciones(payload.dict())


@router.post("/{nombre_banco}/CICuentas")
async def ci_cuentas(nombre_banco: str, payload: CICuentasRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.ci_cuentas(payload.dict())


@router.post("/{nombre_banco}/MBc2p")
async def mb_c2p(nombre_banco: str, payload: R4C2PRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.mb_c2p(payload.dict())


@router.post("/{nombre_banco}/MBanulacionC2P")
async def mb_anulacion_c2p(nombre_banco: str, payload: R4AnulacionC2PRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.mb_anulacion_c2p(payload.dict())


@router.post("/{nombre_banco}/verifico_pago")
async def verifico_pago(nombre_banco: str, payload: VerificoPagoRequest):
    servicio = get_service_for_bank(nombre_banco)
    return await servicio.verificar_pago(payload.dict())


# Ruta dinámica para endpoints por banco.
# Ejemplo: /api/banesco/Banescobcv  -> mapeará a svc.consultar_tasa
#          /api/0108/provincialbcv -> svc.consultar_tasa
#          /api/0134/banescoconsulta -> svc.consulta_cliente (si existe) o svc.consultar_tasa
@router.post("/{nombre_banco}/{nombre_endpoint}")
async def banco_endpoint_dispatch(nombre_banco: str, nombre_endpoint: str, request: Request):
    """Dispatcher dinámico que resuelve endpoints nombrados por banco.

    Reglas básicas:
    - Para R4 mantenemos las rutas explícitas anteriores (no serán afectadas).
    - Para otros bancos, se soportan dos endpoints por banco:
        1) <alias>bcv -> consultar_tasa
        2) <alias>consulta -> consulta_cliente (si está) o consultar_tasa

    El `alias` se toma de la configuración en `bank_registry`.
    """
    servicio = get_service_for_bank(nombre_banco)

    try:
        config_banco = obtener_config_banco(nombre_banco)
    except Exception:
        config_banco = {"alias": nombre_banco}

    alias_banco = str(config_banco.get("alias", nombre_banco)).lower()
    punto = nombre_endpoint.lower()

    # endpoint para tasa (bcv)
    if punto == f"{alias_banco}bcv" or punto == "mbbcv" or punto.endswith("bcv"):
        payload = await request.json()
        return await servicio.consultar_tasa(payload)

    # endpoint para consulta cliente
    if punto == f"{alias_banco}consulta" or punto.endswith("consulta"):
        payload = await request.json()
        # preferir metodo especifico si existe
        if hasattr(servicio, "consulta_cliente"):
            return await servicio.consulta_cliente(payload)
        # algunos servicios implementaron 'consulta'
        if hasattr(servicio, "consulta"):
            return await servicio.consulta(payload)
        # fallback
        return await servicio.consultar_tasa(payload)

    # Si no se resolvió, devolver 404
    raise HTTPException(status_code=404, detail=f"Endpoint '{nombre_endpoint}' no soportado para banco '{nombre_banco}'")
