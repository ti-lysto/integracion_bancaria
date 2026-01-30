

import logging
from datetime import date
from typing import Dict, Any

logger = logging.getLogger(__name__)

class R4Services:
    """Servicios específicos para operaciones R4"""
    
    @staticmethod
    async def procesar_consulta_bcv(moneda: str, fecha_valor: str) -> Dict[str, Any]:
        """Procesar consulta de tasa BCV"""
        
        try:
            from core.config import Config
            import httpx
            
            #MODO DEBUG: Usar tasa simulada
            # if Config.DEBUG:
            #     logger.info(f"Modo DEBUG: Usando tasa simulada para {moneda} - {fecha_valor}")
            #     return {
            #         "code": "00",
            #         "fechavalor": date.today().isoformat(),
            #         "tipocambio": 236.5314
            #     }
            
            # MODO PRODUCCIÓN: Consultar al banco según especificación R4
            logger.info(f"Consultando tasa BCV al banco R4 para {moneda} - {fecha_valor}")
            
            # Validaciones según documento
            if not moneda or not fecha_valor:
                return {
                    "code": "01",
                    "fechavalor": fecha_valor,
                    "tipocambio": 0.0
                }
            
            # CONSULTA AL BANCO SEGÚN ESPECIFICACIÓN R4
            try:
                # URL del banco según documento R4 V3.0
                banco_url = f"{Config.R4_BANCO_URL}/MBbcv"
                
                # Headers según especificación
                #from app.core.security import r4_security
                from core.auth import r4_authentication
                
                # Datos para HMAC según documento: "fechavalor + moneda"
                hmac_data = f"{fecha_valor}{moneda}"
                # Generar firma usando el consolidado `r4_authentication`.
                hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
                # Antes: hmac_signature = r4_security.generate_response_signature({"data": hmac_data})
                logger.info(f"HMAC Data generado: {hmac_signature}")

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
                
                # Log para debugging
                logger.info(f"Enviando al banco: URL={banco_url}")
                logger.info(f"HMAC Data: {hmac_data}")
                logger.info(f"HMAC Signature: {hmac_signature}")
                logger.info(f"Headers: {headers}")
                logger.info(f"Payload: {payload}")

                # Realizar consulta al banco
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(banco_url, json=payload, headers=headers)
                    logger.info(f"Consulta enviada al banco R4. URL={banco_url} Payload={payload} Headers={headers}")
                    logger.info(f"Respuesta del banco: Status={response.status_code}, Body={response.text}")
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Respuesta según especificación: {"code": "00", "fechavalor": "2024-07-23", "tipocambio": 36.5314}
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
            logger.error(f"Error crítico en consulta BCV: {str(e)}")
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
            # guardo en la tabla de transito la intencion de pago
            from db import connector as connector
            filtros_sp = {
                "idcliente": id_cliente,
                "monto": monto or "",
                "TelefonoComercio": telefono or ""
            }
            datos_identificadores={
                "endpoint": endpoint
            }
            respuesta = await connector.guardar_transito_sp(filtros_sp, datos_identificadores)
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
            
            # PASO 1: VALIDACIÓN INICIAL
            codigo_red = datos.get("CodigoRed", "")
            
            # Solo procesar si el código es "00" 
            # if codigo_red != "00":
            #     logger.warning(f"Pago rechazado - Código: {codigo_red}")
            #     return {"abono": False}
            
            # PASO 2: GUARDAR EN BASE DE DATOS usando tu SP real
            resultado = await repository.guardar_transaccion_sp(datos)
            
            # PASO 3: ANALIZAR RESULTADO DEL SP
            # out_params = resultado.get("out_params", ["", 0])
            
            # if len(out_params) >= 2:
            #     mensaje_sp = out_params[0] if out_params[0] else ""
            #     codigo_sp = out_params[1] if out_params[1] else 0
                
            #     logger.info(f"SP Result - Mensaje: {mensaje_sp}, Código: {codigo_sp}")
                
            #     # Si el SP devuelve código positivo, aceptamos el abono
            #     abono = codigo_sp > 0
            # else:
            #     # Si no hay parámetros OUT, asumimos éxito
            #     abono = True
            out_params = resultado.get("out_params", {})
        
            # Obtener valores de los parámetros OUT por nombre
            mensaje_sp = out_params.get("p_mensaje", "")
            codigo_sp = out_params.get("p_codigo", 0)
            
            logger.info(f"SP Result - Mensaje: {mensaje_sp}, Código: {codigo_sp}")
            
            # Si el SP devuelve código positivo, aceptamos el abono
            abono = codigo_sp ==1 #if codigo_sp else True
            # if codigo_sp == 1: abono== True
            # else :abono== False
            
            return{"abono": abono, "mensaje": mensaje_sp, "codigo": codigo_sp} 
            
        except Exception as e:
            logger.error(f"Error procesando notificación: {str(e)}")
            # En caso de error, rechazamos el abono por seguridad
            return {"abono": False}
    
    @staticmethod
    async def procesar_gestion_pagos(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar dispersión de pagos"""
        try:
            # IMPLEMENTAR: Validar suma de montos y procesar dispersión
            monto_total = float(datos.get("monto", "0"))
            personas = datos.get("personas", [])
            
            suma_parciales = sum(float(p.get("montoPart", "0")) for p in personas)
            
            if abs(monto_total - suma_parciales) < 0.01:  # Tolerancia de centavos
                return {
                    "success": True,
                    "message": "Dispersión exitosa"
                }
            else:
                return {
                    "success": False,
                    "message": "Error: suma de montos no coincide"
                }
                
        except Exception as e:
            logger.error(f"Error en gestión pagos: {str(e)}")
            return {
                "success": False,
                "message": f"Error procesando dispersión: {str(e)}"
            }

    @staticmethod
    async def verificar_pago(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar un pago: opcionalmente consulta banco y cruza con BD."""
        from db import connector as repository

        filtros_sp = {
            "Telefono": payload.get("Telefono", ""),
            "Banco": payload.get("Banco", ""),
            "Monto": payload.get("Monto", ""),
            "FechaHora": payload.get("FechaHora", ""),
            "Referencia": payload.get("Referencia")
        }

                
        bd_result = await repository.consultar_notificacion_por_referencia(filtros_sp)
        print ("bd_result:", bd_result)
        # Inicializar variables
        telefono = ""
        banco = ""
        monto = ""
        fecha_hora = ""
        referencia = ""
        encontrado = False
        
        # Verificar si la consulta fue exitosa
        if bd_result and bd_result.get("exito", False):
            resultados = bd_result.get("resultados", [])
            print("resultados crudos:", resultados)
            
            if resultados:
                # Los resultados están en una lista que contiene tuplas
                # Estructura: [((col1, col2, col3, ...),)]
                for resultado_set in resultados:
                    if isinstance(resultado_set, tuple):
                        for fila_tupla in resultado_set:
                            if isinstance(fila_tupla, tuple) and len(fila_tupla) >= 9:
                                # Mapear según la estructura de la tabla r4_notifications:
                                # [0] IdComercio, [1] TelefonoComercio, [2] TelefonoEmisor, 
                                # [3] Concepto, [4] BancoEmisor, [5] Monto,
                                # [6] FechaHora, [7] Referencia, [8] CodigoRed
                                
                                telefono = fila_tupla[2] if len(fila_tupla) > 2 else ""  # TelefonoEmisor
                                banco = fila_tupla[4] if len(fila_tupla) > 4 else ""     # BancoEmisor
                                monto = fila_tupla[5] if len(fila_tupla) > 5 else ""
                                fecha_hora = fila_tupla[6] if len(fila_tupla) > 6 else ""
                                referencia = fila_tupla[7] if len(fila_tupla) > 7 else ""
                                
                                encontrado = bool(referencia)
                                print(f"Fila procesada - Tel: {telefono}, Banco: {banco}, Monto: {monto}")
                                break  # Tomar solo el primer resultado
        
        print(f"telefono: {telefono}, banco: {banco}, monto: {monto}, fecha_hora: {fecha_hora}, referencia: {referencia}, encontrado: {encontrado}")
        
        return {
            "Telefono": telefono or "",
            "Banco": banco or "",
            "Monto": str(monto or ""),
            "FechaHora": fecha_hora or "",
            "Referencia": referencia or "",
            "encontrado": encontrado
        }

    @staticmethod
    async def comprobar_pago(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar un pago: opcionalmente consulta banco y cruza con BD."""
        from db import connector as repository

        filtros_sp = {
            "Telefono": payload.get("Telefono", ""),
            "Banco": payload.get("Banco", ""),
            "Monto": payload.get("Monto", ""),
            "FechaHora": payload.get("FechaHora", ""),
            "Referencia": payload.get("Referencia")
        }

                
        bd_result = await repository.proceso_comprobacion_por_referencia(filtros_sp)
        print ("bd_result:", bd_result)
        
        out_params = bd_result.get("parametros_out", {})
        print("out_params:", out_params)
        procesado= bool(out_params.get("p_procesado", 0))
        print("procesado:", procesado)  
        mensaje= out_params.get("p_mensaje", "")
        print("mensaje:", mensaje)
        
        return {
            "procesado": procesado,
            "mensaje": mensaje
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

                if response.status_code != 200:
                    return {
                        "code": "01",
                        "message": f"Error HTTP {response.status_code}",
                        "reference": ""
                    }

                data = response.json()
                if data.get("code") == "00":
                    return {
                        "code": "00",
                        "message": data.get("message", "TRANSACCION EXITOSA"),
                        "reference": data.get("reference", "")
                    }

                return {
                    "code": data.get("code", "01"),
                    "message": data.get("message", "Error"),
                    "reference": data.get("reference", "")
                }

        except Exception as e:
            logger.error(f"Error procesando vuelto: {str(e)}")
            return {"code": "08", "message": "Error procesando vuelto", "reference": ""}

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

            # Firma según especificación: Banco + Monto + Teléfono + Cedula
            hmac_data = f"{banco}{monto}{telefono}{cedula}"
            
            hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": hmac_signature,
                "Commerce": Config.R4_MERCHANT_ID
            }
            print("payload:", payload)
            print("hmac_data:", hmac_data)
            print("hmac_signature:", hmac_signature)  

            body = {
                "banco": banco,
                "monto": monto,
                "telefono": telefono,
                "cedula": cedula
            }

            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.post(banco_url, json=body, headers=headers)
                logger.info(f"OTP solicitado. URL={banco_url} Payload={body} Headers={headers} Status={response.status_code}")

                if response.status_code != 200:
                    return {
                        "code": "01",
                        "message": f"Error HTTP {response.status_code}",
                        "success": False
                    }

                data = response.json()
                if data.get("code") == "202":
                    return {
                        "code": "202",
                        "message": data.get("message"),
                        "success": data.get("success")
                    }

                return {
                    "code": data.get("code", "01"),
                    "message": data.get("message", "Error generando OTP"),
                    "success": data.get("success", False)
                }

        except Exception as e:
            logger.error(f"Error procesando OTP: {str(e)}")
            return {"code": "08", "message": "Error procesando OTP", "success": False}


