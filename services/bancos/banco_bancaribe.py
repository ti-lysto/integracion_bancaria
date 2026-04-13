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
                    print (f"Intento {intento} - respuesta token de Bancaribe: {respuesta}")   
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
            
            return {"error": f"No se pudo consultar operaciones en Bancaribe luego de {get_bancaribe_config().get('reintentos', 0)+1} intentos"}
        except Exception as exc:
            logger.error(f"Error consultando operaciones en Bancaribe: {exc}")
            return {"error": "Error interno al consultar operaciones en Bancaribe"} 
        
    @staticmethod
    async def bcv(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta tasa BCV en Bancaribe, con fallback seguro si falla el banco."""

        tokenresponse=await BancoBancaribeService.solicito_token()
        token=tokenresponse.get("access_token")
        header=BancoBancaribeService._build_headers("consultaoperaciones", token)
        url=get_bancaribe_config().get("bc_bcv_url")
        if not url:
            logger.error("URL de consulta BCV no configurada en bancaribe_config")
            return {"error": "URL de consulta BCV no configurada"}
        body={
            "hash": get_bancaribe_config().get("hash"),
            "idTasa": "TACOMPDOLAR" if payload.get("Moneda") == "USD" else "TACOMPEURO" if payload.get("Moneda") == "EUR" else ""   ,
            "cedulaRif": Config.RIF.replace("-",""),
            "fechaInicio": payload.get("FechaInicio", "").replace("-","/"),
            "fechaFin": payload.get("FechaFin", "").replace("-","/")
        }
        # print (f"URL de consulta BCV: {url} Payload: {body}")
        import httpx
        try:
            for intento in range(int(get_bancaribe_config().get("reintentos", 0)) ):
                try:
                    # print (f" Consultando BCV a Bancaribe, url: {url} body: {body} header: {header}")
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, json=body, headers=header)
                    if response.status_code < 400:
                        # print (f"Respuesta BCV de Bancaribe: {response}")
                        return response.json().get("listTasasActuales") if response.json().get("listTasasActuales") else response.json().get("listTasaHistorico", {})
                except Exception as exc:
                    logger.error(f"Error en intento {intento} consultando BCV a Bancaribe: {exc}")
                    continue
            
        except Exception as exc:
            logger.error(f"Error consultando BCV en Bancaribe: {exc}")
            return {"error": "Error interno al consultar BCV en Bancaribe"}
        return {"error": "No se pudo obtener tasa BCV de Bancaribe después de todos los intentos"}


