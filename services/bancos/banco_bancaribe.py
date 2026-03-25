"""Servicio de integracion para Banco Bancaribe (codigo 0114)."""

from __future__ import annotations

from typing import Any, Dict, Optional
import base64,json,logging


from core.config import get_bancaribe_config,Config

logger = logging.getLogger(__name__)


class BancoBancaribeService:
    """Servicio Bancaribe con estructura alineada al patron de R4."""

    @staticmethod
    def _get_config() -> Dict[str, Any]:
        return get_bancaribe_config()
    
    @staticmethod
    def _build_headers(endpoint: str, token: Optional[str]="") -> Dict[str, str]:        
                
        match endpoint:
            case "token":
                calculo = BancoBancaribeService.calcular_base64_bancaribe()
                return {
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {calculo}"
                }
            case "consultaoperaciones":
                
                return {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer Token {token}"
                }
            case _:
                return {"Content-Type": "application/json"}   

    @staticmethod
    def calcular_base64_bancaribe() -> str:
        """Genera token Basic con consumer_key y consumer_secret."""
        config = BancoBancaribeService._get_config()
        consumer_key = config.get("consumer_key") or ""
        consumer_secret = config.get("consumer_secret") or ""

        if not consumer_key or not consumer_secret:
            raise ValueError("Faltan BC_CONSUMER_KEY o BC_CONSUMER_SECRET en la configuracion")

        raw = f"{consumer_key}:{consumer_secret}"
        return base64.b64encode(raw.encode("utf-8")).decode("utf-8")
        
    @staticmethod   
    async def solicito_token ()->Dict[str, Any]:
        """Endpoint para solicitar token de autenticación (si se requiere)."""
        try:
            import httpx
            token = BancoBancaribeService.calcular_base64_bancaribe()
            header=BancoBancaribeService._build_headers("token")
            body = {"grant_type":"client_credentials"}
            url=get_bancaribe_config().get("token_url")  
            if not url:
                logger.error("URL de token no configurada en bancaribe_config")
                return {"error": "URL de token no configurada"}
            for intento in range(int(get_bancaribe_config().get("reintentos", 0)) ):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, json=body, headers=header)
                    respuesta = response.json() 
                    # print (f"Intento {intento} - token: {respuesta.get('access_token')if respuesta else 'No se obtuvo token'}")   
                    if respuesta.get("access_token") and response.status_code < 400:
                        return {**respuesta}
                except Exception as exc:
                    logger.error(f"Error en intento {intento} solicitando token a Bancaribe: {exc}")
                    continue 
                logger.error(f"Error solicitando token a Bancaribe: {response.status_code} - {response.text}")
            return {"error": "No se pudo obtener token de Bancaribe"} 
        except Exception as exc:
            logger.error(f"Error generando token de Bancaribe: {exc}")
            return {"error": "No se pudo generar token"}

    @staticmethod
    async def procesar_notificacion(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper compatible con endpoints existentes."""
        from db import connector as repository
        return await repository.proceso_notificaciones(payload, banco="BanCaribe")
    
        logger.info(f"Notificacion recibida en BancoBancaribeService: {json.dumps(payload)}")
        return {"message": "Success", "statusCode": 200}

    @staticmethod
    async def consulta_operaciones(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper compatible con endpoints existentes."""
        tokenresponse=await BancoBancaribeService.solicito_token()
        token=tokenresponse.get("access_token")
        header=BancoBancaribeService._build_headers("consultaoperaciones", token)
        url=get_bancaribe_config().get("consulta_url")
        body={
            "tipoTrx": "PM",
            "rif": Config.RIF,
            "referencia": payload.get("referencia"),
            "montoTransaccion": payload.get("montoTransaccion"),
            "identificadorPersona": payload.get("ci", "E82220074"),
            "telefonoDebito": payload.get("telefono", ""),
            "factura": "",
            "fecha": payload.get("fecha", "")
        }
        #print (f"URL de consulta operaciones: {url} Header: {header} Payload: {payload}")
        if not url:
            logger.error("URL de consulta operaciones no configurada en bancaribe_config")
            return {"error": "URL de consulta operaciones no configurada"}
        try:
            import httpx
            for intento in range(int(get_bancaribe_config().get("reintentos", 0)) ):
                try:
                    # print (f"Intento {intento} - Consultando operaciones a Bancaribe ")
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, json=body, headers=header)
                    if response.status_code < 400:
                        return response.json() if response.text else {}
                except Exception as exc:
                    logger.error(f"Error en intento {intento} consultando operaciones a Bancaribe: {exc}")
                    continue
            # if response.status_code >= 400:
            #     logger.error(f"Error consultando operaciones a Bancaribe: {response.status_code} - {response.text}")
            #     return {"error": "No se pudo consultar operaciones en Bancaribe"}
            return {"error": f"No se pudo consultar operaciones en Bancaribe luego de {get_bancaribe_config().get('reintentos', 0)+1} intentos"}
        except Exception as exc:
            logger.error(f"Error consultando operaciones en Bancaribe: {exc}")
            return {"error": "Error interno al consultar operaciones en Bancaribe"} 
        
    @staticmethod
    async def bcv(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta tasa BCV en Bancaribe, con fallback seguro si falla el banco."""

        # tokenresponse=await BancoBancaribeService.solicito_token()
        # token=tokenresponse.get("access_token")
        # header=BancoBancaribeService._build_headers("consultaoperaciones", token)
        url=get_bancaribe_config().get("bc_bcv_url")
        body={
            "hash": get_bancaribe_config().get("hash"),
            "idTasa": "TACOMPDOLAR" if payload.get("moneda") == "USD" else "TACOMPEURO" if payload.get("moneda") == "EUR" else ""   ,
            #"idTasa": "",
            "cedulaRif": Config.RIF.replace("-",""),
            "fechaInicio": payload.get("fechaInicio", ""),
            "fechaFin": payload.get("fechaFin", "")
        }
        print (f"URL de consulta BCV: {url} Payload: {payload}")
        return {"payload": payload, "body": body}
    



        #print (f"URL de consulta operaciones: {url} Header: {header} Payload: {payload}")
        # if not url:
        #     logger.error("URL de consulta operaciones no configurada en bancaribe_config")
        #     return {"error": "URL de consulta operaciones no configurada"}
        # try:
        #     import httpx
        #     for intento in range(int(get_bancaribe_config().get("reintentos", 0)) ):
        #         try:
        #             # print (f"Intento {intento} - Consultando operaciones a Bancaribe ")
        #             async with httpx.AsyncClient() as client:
        #                 response = await client.post(url, json=body, headers=header)
        #             if response.status_code < 400:
        #                 return response.json() if response.text else {}
        #         except Exception as exc:
        #             logger.error(f"Error en intento {intento} consultando operaciones a Bancaribe: {exc}")
        #             continue
        #     return {"error": f"No se pudo consultar operaciones en Bancaribe luego de {get_bancaribe_config().get('reintentos', 0)+1} intentos"}
        # except Exception as exc:
        #     logger.error(f"Error consultando operaciones en Bancaribe: {exc}")
        #     return {"error": "Error interno al consultar operaciones en Bancaribe"} 
        
    




    # @staticmethod
    # def _map_bcv_response(data: Dict[str, Any], fecha_valor: str) -> Dict[str, Any]:
    #     code = str(data.get("code") or data.get("codigo") or "01")
    #     tipo_cambio_raw = data.get("tipocambio", data.get("tasa", 0.0))
    #     try:
    #         tipo_cambio = float(tipo_cambio_raw)
    #     except (TypeError, ValueError):
    #         tipo_cambio = 0.0

    #     return {
    #         "code": code,
    #         "fechavalor": str(data.get("fechavalor") or fecha_valor),
    #         "tipocambio": tipo_cambio,
    #     }

    # @staticmethod
    # async def procesar_consulta_bcv(moneda: str, fecha_valor: str) -> Dict[str, Any]:
    #     """Consulta tasa BCV en Bancaribe, con fallback seguro si falla el banco."""
    #     logger.info("Consultando tasa BCV en Bancaribe para %s - %s", moneda, fecha_valor)

    #     if not moneda or not fecha_valor:
    #         return {"code": "01", "fechavalor": fecha_valor or "", "tipocambio": 0.0}

    #     config = BancoBancaribeService._get_config()
    #     consulta_url = config.get("consulta_url")

    #     if not consulta_url:
    #         logger.warning("BC_CONSULTA_DE_OPERACIONES_URL no configurada, devolviendo fallback")
    #         return {"code": "01", "fechavalor": fecha_valor, "tipocambio": 0.0}

    #     payload = {
    #         "Moneda": str(moneda).upper(),
    #         "Fechavalor": fecha_valor,
    #     }

    #     try:
    #         import httpx

    #         headers = BancoBancaribeService._build_headers("")
    #         async with httpx.AsyncClient(timeout=config.get("timeout", 30)) as client:
    #             response = await client.post(consulta_url, json=payload, headers=headers)

    #         logger.info(
    #             "Consulta BCV Bancaribe enviada. URL=%s Status=%s",
    #             consulta_url,
    #             response.status_code,
    #         )

    #         if response.status_code >= 400:
    #             logger.error("Error HTTP Bancaribe consulta BCV: %s - %s", response.status_code, response.text)
    #             return {"code": "01", "fechavalor": fecha_valor, "tipocambio": 0.0}

    #         data = response.json() if response.text else {}
    #         return BancoBancaribeService._map_bcv_response(data, fecha_valor)

    #     except Exception as exc:
    #         logger.error("Error consultando BCV en Bancaribe: %s", exc)
    #         return {"code": "01", "fechavalor": fecha_valor, "tipocambio": 0.0}

    # @staticmethod
    # async def procesar_consulta_cliente(
    #     id_cliente: str,
    #     monto: str | None = None,
    #     telefono: str | None = None,
    #     endpoint: str = "",
    # ) -> Dict[str, Any]:
    #     """Consulta de cliente alineada al contrato R4 (retorna {'status': bool})."""
    #     try:
    #         logger.info(
    #             "Consulta cliente Bancaribe id=%s monto=%s telefono=%s endpoint=%s",
    #             id_cliente,
    #             monto,
    #             telefono,
    #             endpoint,
    #         )
    #         return {"status": bool(id_cliente)}
    #     except Exception as exc:
    #         logger.error("Error en consulta cliente Bancaribe: %s", exc)
    #         return {"status": False}

    # @staticmethod
    # async def procesar_notificacion_pago(datos: Dict[str, Any]) -> Dict[str, Any]:
    #     """Procesa notificacion y persiste con el mismo patron usado en R4."""
    #     try:
    #         from db import connector as repository

    #         resultado = await repository.guardar_transaccion_sp(datos)
    #         out_params = resultado.get("out_params", {}) if isinstance(resultado, dict) else {}
    #         mensaje_sp = out_params.get("p_mensaje", "")
    #         codigo_sp = out_params.get("p_codigo", 0)
    #         abono = codigo_sp == 1

    #         logger.info(
    #             "Notificacion Bancaribe procesada. codigo=%s mensaje=%s",
    #             codigo_sp,
    #             mensaje_sp,
    #         )
    #         return {"abono": abono, "mensaje": mensaje_sp, "codigo": codigo_sp}
    #     except Exception as exc:
    #         logger.error("Error procesando notificacion Bancaribe: %s", exc)
    #         return {"abono": False, "mensaje": "error interno", "codigo": 0}

    # @staticmethod
    # async def consultar_tasa(payload: Dict[str, Any]) -> Dict[str, Any]:
    #     """Wrapper compatible con endpoints existentes."""
    #     # consultar token
    #     token= await BancoBancaribeService.solicito_token({})
    #     access_token = token.get("access_token") if token else None
    #     if not access_token:
    #         logger.error("No se pudo obtener access_token para consulta BCV en Bancaribe")
    #         return {"code": "01", "fechavalor": payload.get("Fechavalor", ""), "tipocambio": 0.0}
        
    #     return await BancoBancaribeService.procesar_consulta_bcv(
    #         payload.get("Moneda", ""),
    #         payload.get("Fechavalor", ""),
    #     )

    # @staticmethod
    # async def consulta_cliente(payload: Dict[str, Any]) -> Dict[str, Any]:
    #     """Wrapper compatible con endpoints existentes."""
    #     return await BancoBancaribeService.procesar_consulta_cliente(
    #         payload.get("IdCliente", ""),
    #         payload.get("Monto"),
    #         payload.get("TelefonoComercio"),
    #         payload.get("endpoint", ""),
    #     )

    