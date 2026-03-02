

import logging
from datetime import date
from typing import Dict, Any
from core.config import get_r4_config 

logger = logging.getLogger(__name__)
r4_config = get_r4_config()
class R4Services:
    """Servicios específicos para operaciones R4"""
    
    @staticmethod
    async def procesar_consulta_bcv(moneda: str, fecha_valor: str) -> Dict[str, Any]:
        """Procesar consulta de tasa BCV"""
        
        try:
            from core.config import Config
            import httpx
                        
            logger.info(f"Consultando tasa BCV al banco R4 para {moneda} - {fecha_valor}")
            
            # Validaciones según documento
            if not moneda or not fecha_valor:
                return {
                    "code": "01",
                    "fechavalor": fecha_valor,
                    "tipocambio": 0.0
                }
                        
            try:                
                banco_url = f"{Config.R4_BANCO_URL}/MBbcv"
                
                from core.auth import r4_authentication
                
                hmac_data = f"{fecha_valor}{moneda}"
                hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": hmac_signature,
                    "Commerce": Config.R4_MERCHANT_ID
                }
                
                # Payload según especificación
                payload = {
                    "Moneda": moneda.upper(),
                    "Fechavalor": fecha_valor
                }
                

                # Realizar consulta al banco
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(banco_url, json=payload, headers=headers)
                    logger.info(f"Consulta enviada al banco R4. URL={banco_url} Payload={payload}")
                    logger.info(f"Respuesta del banco: Status={response.status_code}, Body={response.text}")
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("code") == "00":
                            logger.info(f"Tasa BCV obtenida del banco: {data.get('tipocambio')} VES/{moneda}")
                            return {
                                "code": "00",
                                "fechavalor": data.get("fechavalor", fecha_valor),
                                "tipocambio": float(data.get("tipocambio", 0.0))
                            }
                        else:
                            logger.warning(f"Banco devolvió error: {data.get('code')}")
                            return {
                                "code": data.get("code", "01"),
                                "fechavalor": fecha_valor,
                                "tipocambio": 0.0
                            }
                    else:
                        logger.error(f"Error HTTP del banco: {response.status_code}")
                        return {
                            "code": "01",
                            "fechavalor": fecha_valor,
                            "tipocambio": 0.0
                        }
                        
            except Exception as banco_error:
                logger.error(f"Error consultando banco R4: {banco_error}")
                
                return {
                    "code": "01",
                    "fechavalor": fecha_valor,
                    "tipocambio": 0.0
                }
            
        except Exception as e:
            logger.error(f"Error interno crítico en consulta BCV: {str(e)}")
            return {
                "code": "01",
                "fechavalor": fecha_valor,
                "tipocambio": 0.0
            }
    
    @staticmethod
    async def procesar_consulta_cliente(id_cliente: str, monto: str | None = None, telefono: str | None = None, endpoint: str = "") -> Dict[str, Any]:
        """Procesar consulta de cliente"""
        try:
            # Siempre se va adevolver el valor True.
            # el fujo es: en esta etapa existe una intencion de pago
            # y se asume que el cliente es valido para continuar.
            # es decir, aceptamos todos las inteinciones de pago.
            from core.config import Config            
            cliente_valido = True
            if Config.DEBUG:
                logger.info(f"Consulta cliente {id_cliente} - Valido: {cliente_valido}")
            return {"status": cliente_valido}
        except Exception as e:
            logger.error(f"Error en consulta cliente: {str(e)}")
            return {"status": False}
    
    @staticmethod
    async def procesar_notificacion_pago(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar notificación de pago móvil usando SP real"""
        try:
            from db import connector as repository
            
            
            #GUARDAR EN BASE DE DATOS
            resultado = await repository.guardar_transaccion_sp(datos)
            logger.info(f"notificación de pago procesada. datos: {datos} Resultado SP: {resultado}")
            out_params = resultado.get("out_params", {})
        
            # Obtener valores de los parámetros OUT por nombre
            mensaje_sp = out_params.get("p_mensaje", "")
            codigo_sp = out_params.get("p_codigo", 0)
            
            logger.info(f"SP Result - Mensaje: {mensaje_sp}, Código: {codigo_sp}")
            
            # Si el SP devuelve código positivo, aceptamos el abono
            abono = codigo_sp ==1 
            
            return{"abono": abono, "mensaje": mensaje_sp, "codigo": codigo_sp} 
            
        except Exception as e:
            logger.error(f"Error procesando notificación: {str(e)}")
            # En caso de error, rechazamos el abono por seguridad
            return {"abono": False}
    
    @staticmethod
    async def procesar_gestion_pagos(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar dispersión de pagos"""
        try:
            from core.config import Config
            import httpx
            from core.auth import r4_authentication
            banco_url = f"{Config.R4_BANCO_URL}/R4pagos"
            # Firma según especificación: Monto + Fecha + Referencia + concatenación de montos parciales
            monto = datos.get("monto")
            fecha = datos.get("fecha")
            referencia = datos.get("Referencia")
            personas = datos.get("personas", [])
            concatenacion_montos = "".join(p.get("montoPart") for p in personas)
            
            hmac_data = f"{monto}{fecha}{referencia}{concatenacion_montos}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }
            body = datos
            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
                logger.info(f"Dispersión solicitada R4pagos. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code} respuesta: {response.text}")
                data = response.json()
                # falta guardar en base de datos el resultado de la gestión de pagos
                return {
                    "error": data.get("error",""),
                    "success": data.get("success",""),
                    "message": data.get("message","")
                }
            
        except Exception as e:
            logger.error(f"Error interno en gestión pagos: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "message": f"Error interno procesando dispersión: {str(e)}"
            }

    @staticmethod
    async def verificar_pago(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar un pago: opcionalmente consulta banco y cruza con BD."""
        try: 
            from db import connector as repository

            telefono = ""
            banco = ""
            monto = ""
            fecha_hora = ""
            referencia = ""
            encontrado = False
            id_val = ""

            filtros_sp = {
                "Telefono": payload.get("Telefono", ""),
                "Banco": payload.get("Banco", ""),
                "Monto": payload.get("Monto", ""),
                "FechaHora": payload.get("FechaHora", ""),
                "Referencia": payload.get("Referencia"),
                "Id": payload.get("Id", "" )
            }

                    
            bd_result = await repository.consultar_notificacion_por_referencia(filtros_sp)
            logger.info(f"verificar pago solicitado datos: {filtros_sp} -  resultado : {bd_result}")
            
            # Verificar si la consulta fue exitosa
            if bd_result and bd_result.get("exito", False):
                resultados = bd_result.get("resultados", [])
                #print("resultados crudos:", resultados)
                
                resultados = bd_result.get("resultados") or []
                primer_set = resultados[0] if resultados else ()
                fila = primer_set[0] if primer_set else None

                if fila:
                    # Indices del SP esperado en orden: IdComercio, TelefonoComercio,
                    # TelefonoEmisor, Concepto, BancoEmisor, Monto, FechaHora,
                    # Fecha, Referencia, CodigoRed, Procesado.
                    telefono = fila[2] if len(fila) > 2 else ""
                    banco = fila[4] if len(fila) > 4 else ""
                    monto = fila[5] if len(fila) > 5 else ""
                    fecha_hora = fila[7] if len(fila) > 7 else ""
                    referencia = fila[8] if len(fila) > 8 else ""
                    id_val = fila[0] if len(fila) > 0 else ""
                    encontrado = bool(referencia)
            return {
                "Telefono": telefono or "",
                "Banco": banco or "",
                "Monto": str(monto or ""),
                "FechaHora": fecha_hora or "",
                "Referencia": referencia or "",
                "encontrado": encontrado,
                "Id": id_val or ""
            }
        except Exception as e:
            logger.error(f"Error interno en verificación de pago: {str(e)}")
            return {
                "Telefono": "",
                "Banco": "",
                "Monto": "",
                "FechaHora": "",
                "Referencia": "",
                "encontrado": False,
                "Id": ""
            }

    @staticmethod
    async def comprobar_pago(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar un pago: opcionalmente consulta banco y cruza con BD."""
        
        try:
            from db import connector as repository
            filtros_sp = {
                "Telefono": payload.get("Telefono", ""),
                "Banco": payload.get("Banco", ""),
                "Monto": payload.get("Monto", ""),
                "FechaHora": payload.get("FechaHora", ""),
                "Referencia": payload.get("Referencia")
            }

                    
            bd_result = await repository.proceso_comprobacion_por_referencia(filtros_sp)
            logger.info(f"comprobar pago solicitado datos: {filtros_sp} -  resultado : {bd_result}")
            
            out_params = bd_result.get("parametros_out", {})
            procesado= bool(out_params.get("p_procesado", 0))
            mensaje= out_params.get("p_mensaje", "")
            
            return {
                "procesado": procesado,
                "mensaje": mensaje
            }
        except Exception as e:
            logger.error(f"Error interno en comprobación de pago: {str(e)}")
            return {
                "procesado": False,
                "mensaje": f"Error interno procesando comprobación: {str(e)}"
            }

    @staticmethod    
    async def procesar_vuelto(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar vuelto de pago móvil: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            banco_url = f"{Config.R4_BANCO_URL}/MBvuelto"

            telefono = payload.get("TelefonoDestino")
            monto = payload.get("Monto")
            banco = payload.get("Banco")
            cedula = payload.get("Cedula")
            concepto = payload.get("Concepto")
            ip_origen = payload.get("Ip")

            # Firma según especificación: TelefonoDestino + Monto + Banco + Cedula
            hmac_data = f"{telefono}{monto}{banco}{cedula}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }

            body = {
                "TelefonoDestino": telefono,
                "Cedula": cedula,
                "Banco": banco,
                "Monto": monto
            }

            if concepto:
                body["Concepto"] = concepto
            if ip_origen:
                body["Ip"] = ip_origen

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
                logger.info(f"Vuelto solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
                data = response.json()
                # falta guardar en base de datos el resultado del vuelto
                return {
                    "code": data.get("code"),
                    "message": data.get("message"),
                    "reference": data.get("reference")
                }

        except Exception as e:
            logger.error(f"Error interno procesando vuelto: {str(e)}")
            return {"code": "08", "message": "Error interno procesando vuelto", "reference": ""}

    @staticmethod
    async def procesar_otp(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar generación de OTP: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            banco_url = f"{Config.R4_BANCO_URL}/GenerarOtp"
            
            banco = payload.get("Banco")
            monto = payload.get("Monto")
            telefono = payload.get("Telefono")
            cedula = payload.get("Cedula")

            hmac_data = f"{banco}{monto}{telefono}{cedula}"            
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }
            
            body = {
                "banco": banco,
                "monto": monto,
                "telefono": telefono,
                "cedula": cedula
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
                logger.info(f"OTP solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
                data = response.json()
                from db import connector as connector
                resutado = await connector.guardar_transito_sp({
                        "TelefonoContacto": telefono,
                        "Banco": banco,
                        "Monto": monto,
                        "Cedula": cedula,
                        "Otp": data.get("otp"),
                        "respuesta":data.get("message"),
                        "endpoint": "GenerarOtp",
                        
                    }, {
                        "TelefonoContacto": telefono,
                        "Banco": banco,
                        "Monto": monto,
                        "Cedula": cedula,
                        "Otp": data.get("otp")
                    },
                        {"GenerarOtp": {"solicitud": payload, "respuesta": data}}
                    )
                
                return {
                    "code": data.get("code"),
                    "message": data.get("message"),
                    "success": bool(data.get("success"))
                }

        except Exception as e:
            logger.error(f"Error procesando OTP: {str(e)}")
            return {"code": "08", "message": "Error procesando OTP", "success": False}

    @staticmethod
    async def procesar_debitoinmediato(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar débito inmediato: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            banco_url = f"{Config.R4_BANCO_URL}/DebitoInmediato"

            banco = payload.get("Banco")
            monto = payload.get("Monto")
            telefono = payload.get("Telefono")
            cedula = payload.get("Cedula")  
            nombre = payload.get("Nombre")
            otp = payload.get("OTP")
            concepto = payload.get("Concepto")            

            # Firma según especificación: Banco + Cedula + Telefono + Monto + OTP
            hmac_data = f"{banco}{cedula}{telefono}{monto}{otp}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }

            body = {
                "banco": banco,
                "monto": monto,
                "telefono": telefono,
                "cedula": cedula,
                "nombre": nombre,
                "otp": otp,
                "concepto": concepto
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
            logger.info(f"Débito inmediato solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
            data = response.json()
            from db import connector as connector
            resutado = await connector.guardar_transito_sp({
                    "TelefonoContacto": telefono,
                    "Banco": banco,
                    "Monto": monto,
                    "Cedula": cedula,
                    "OTP": otp,
                    "Respuesta":data.get("message", ""),
                    "endpoint": "DebitoInmediato",
                    #"id_dev_cred": data.get("id"),
                    "id_dev_cred": "6785d97e-2092-49f0-9f7d-3d5921f0b135",
                    "Referencia": data.get("reference"),
                    #"Referencia": "REFerenciatest4",
                    "CodigoRed": data.get("code", "")
                }, {
                    "TelefonoContacto": telefono,
                    "Banco": banco,
                    "Monto": monto,
                    "Cedula": cedula,
                    "OTP": otp
                },                
                {"DebitoInmediato": {"solicitud": payload, "respuesta": data}}
                )
            intentos = 0
            resultado = data
            while resultado.get("code") == "AC00" and intentos < r4_config["reintentos"]:
                print(f"Intento {intentos+1} de consulta de operaciones para Id: {resultado.get('Id')}")
                intentos += 1
                resultado = await R4Services.procesar_consulta_operaciones({"Id": resultado.get("Id")})
            print(f"Resultado final después de {intentos} intentos: {resultado}")
            return {
                    "code": data.get("code"),
                    "message": data.get("message"),
                    "reference": data.get("reference", ""),
                    "Id": data.get("Id", "")
                }
                
        except Exception as e:
            logger.error(f"Error interno procesando débito inmediato: {str(e)}")
            return {"code": "08", "message": "Error procesando OTP", "success": False}

    @staticmethod
    async def procesar_c2p(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar cobro c2p: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            logger.info(f"Procesando C2P con payload: {payload}")
            banco_url = f"{Config.R4_BANCO_URL}/MBc2p"

            telefono = payload.get("TelefonoDestino")
            cedula = payload.get("Cedula")  
            concepto = payload.get("Concepto")            
            banco = payload.get("Banco")
            monto = payload.get("Monto")
            otp = payload.get("Otp")
            

            # Firma según especificación: Banco + Cedula + Telefono + Monto + OTP
            hmac_data = f"{telefono}{monto}{banco}{cedula}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }

            body = {
                "TelefonoContacto": telefono,
                "Cedula": cedula,
                "Concepto": concepto,
                "Banco": banco,
                "Ip": "51.103.216.233", #IP origen la VM por defecto
                "Monto": monto,
                "Otp": otp
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
            logger.info(f"Proceso C2P solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
            data = response.json()
            from db import connector as connector
            resutado = await connector.guardar_transito_sp({
                    "TelefonoContacto": telefono,
                    "Banco": banco,
                    "Monto": monto,
                    "Cedula": cedula,
                    "OTP": otp,
                    "Concepto": concepto,
                    #"respuesta":data.get("message"),
                    #"respuesta":"Operación Aceptada",
                    "endpoint": "C2P",
                    #"id_dev_cred": data.get("Id"),
                    #"id_dev_cred": "6785d97e-2092-49f0-9f7d-3d5921f0b13f",
                    "Referencia": data.get("reference"),
                    #"Referencia": "REF1234567890",
                    "mensaje": data.get("message"),
                    "code": data.get("code")
                }, {
                    "TelefonoContacto": telefono,
                    "Banco": banco,
                    "Monto": monto,
                    "Cedula": cedula,
                    "OTP": otp
                },                
                {"C2P": {"solicitud": payload, "respuesta": data}}
                )
            
            return {
                "message": data.get("message", ""),
                "code": data.get("code",""),                    
                "reference": data.get("reference", "")
            }            
            
        except Exception as e:
            logger.error(f"Error procesando débito inmediato: {str(e)}")
            return {"code": "08", "message": "Error procesando OTP", "success": False}

    @staticmethod
    async def procesar_anulacionc2p(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar anulación de cobro c2p: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            banco_url = f"{Config.R4_BANCO_URL}/MBanulacionC2P"

            cedula = payload.get("Cedula")              
            banco = payload.get("Banco")
            referencia = payload.get("Referencia")          
            

            # Firma según especificación: Banco + Cedula + Telefono + Monto + OTP
            hmac_data = f"{banco}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }

            body = {
                "Cedula": cedula,
                "Banco": banco,
                "Referencia": referencia
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
            logger.info(f"Anulación C2P solicitada. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
            data = response.json()
            from db import connector as connector
            resutado = await connector.guardar_transito_sp({
                    #"TelefonoContacto": telefono,
                    "Banco": banco,
                    #"Monto": monto,
                    "Cedula": cedula,
                    #"OTP": otp,
                    #"Concepto": concepto,
                    #"respuesta":data.get("message"),
                    #"respuesta":"Operación Aceptada",
                    "endpoint": "MBanulacionC2P",
                    #"id_dev_cred": data.get("Id"),
                    #"id_dev_cred": "6785d97e-2092-49f0-9f7d-3d5921f0b13f",
                    #"Referencia": data.get("reference")
                    "Referencia": referencia,
                    "mensaje": data.get("message"),
                    "code": data.get("code"),
                    "anulado": "1"
                }, {
                    "cedula": cedula,
                    "Banco": banco,
                    "Referencia": referencia
                },                
                {"Anulacion C2P": {"solicitud": payload, "respuesta": data}}
                )

            return {
                "code": data.get("code", ""),
                "message": data.get("message", ""),
                "reference": data.get("reference", "")
            }
        except Exception as e:
            logger.error(f"Errorinterno procesando anulación C2P: {str(e)}")
            return {"code": "08", "message": "Error procesando anulación C2P", "success": False}

    @staticmethod
    async def procesar_creditoinmediato(payload: Dict[str, Any]) -> Dict[str, Any]:

        """Procesar crédito inmediato: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            banco_url = f"{Config.R4_BANCO_URL}/CreditoInmediato"

            banco = payload.get("Banco")
            monto = payload.get("Monto")
            telefono = payload.get("Telefono")
            cedula = payload.get("Cedula")
            concepto = payload.get("Concepto")            

            # Firma según especificación: Banco + Cedula + Telefono + Monto
            hmac_data = f"{banco}{cedula}{telefono}{monto}"
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }

            body = {
                "Banco": banco,
                "Cedula": cedula,
                "Telefono": telefono,
                "Monto": monto,
                "Concepto": concepto
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
            logger.info(f"Crédito inmediato solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
            data = response.json()
            from db import connector as connector
            resutado = await connector.guardar_transito_sp({
                    "TelefonoContacto": telefono,
                    "Banco": banco,
                    "Monto": monto,
                    "Cedula": cedula,
                    #"OTP": otp,
                    "Concepto": concepto,
                    #"respuesta":data.get("message"),
                    #"respuesta":"Operación Aceptada",
                    "endpoint": "CreditoInmediato",
                    "id_dev_cred": data.get("Id"),
                    #"id_dev_cred": "6785d97e-2092-49f0-9f7d-3d5921f0b13f",
                    "Referencia": data.get("reference"),
                    #"Referencia": "REF1234567890",
                    "mensaje": data.get("message"),
                    #"code": data.get("code")
                    "CodigoRed": data.get("code", "")
                }, {            
                    "Banco": banco,
                    "Cedula": cedula,
                    "TelefonoContacto": telefono,
                    "Monto": monto,
                    #"Concepto": concepto
                    #"OTP": otp
                },                
                {"CreditoInmediato": {"solicitud": payload, "respuesta": data}}
                )
            
            return {
                "code": data.get("code",""),
                "message": data.get("message",""),
                "reference": data.get("reference", ""),
                "Id": data.get("Id", "")
            }

        except Exception as e:
            logger.error(f"Error interno procesando crédito inmediato: {str(e)}")
            return {"code": "08", "message": "Error procesando crédito inmediato", "success": False}
        
    @staticmethod
    async def procesar_consulta_operaciones(payload: Dict[str, Any]) -> Dict[str,Any]:
        """Procesar consulta de operaciones: arma firma HMAC y envía al banco."""
        from core.config import Config
        import httpx
        from core.auth import r4_authentication

        try:
            
            verificacion = await R4Services.verificar_pago(payload)
            code=""
            mesage=""
            success=False
            data = None
            if not verificacion.get("Referencia"):                
            
                banco_url = f"{Config.R4_BANCO_URL}/ConsultaOperaciones"

                id = payload.get("Id")
                

                # Firma según especificación: id
                hmac_data = f"{id}"
                hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": hmac_signature,
                    "Commerce": Config.R4_MERCHANT_ID
                }

                body = {
                    "Id": id
                }

                async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                    response = await client.post(banco_url, json=body, headers=headers)
                logger.info(f"Consulta de operaciones solicitada. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")
                data = response.json()
                
                from db import connector as connector
                resultado = await connector.guardar_transito_sp({
                        "id_dev_cred": id,
                        "endpoint": "ConsultaOperaciones",
                        "mensaje": data.get("message"),
                        "CodigoRed": data.get("code", ""),
                        "Referencia": data.get("reference", "")
                        #"Referencia": "REFerenciatest7"
                    }, {            
                        "id_dev_cred": id
                    },                
                    {"ConsultaOperaciones": {"solicitud": payload, "respuesta": data}}
                    )
                
                mesage=data.get("message", "")
                success=True
            else:
                mesage="Pago encontrado en BD, no se consulta al banco"


            return {
                "code": data.get("code","") if data else "",
                "reference": data.get("reference","") if data else "",
                "message": mesage,
                "success": success
            }

        except Exception as e:
            logger.error(f"Error interno procesando consulta de operaciones: {str(e)}")
            return {"code": "08", "message": "Error procesando consulta de operaciones", "success": False}




