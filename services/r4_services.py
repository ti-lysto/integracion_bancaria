

import logging
from datetime import date
from typing import Dict, Any

logger = logging.getLogger(__name__)

class R4Services:
    """Servicios específicos para operaciones R4"""
    
    @staticmethod
    async def procesar_consulta_bcv(moneda: str, fecha_valor: str) -> Dict[str, Any]:
        """Procesar consulta de tasa BCV"""
        
        # try:
        #     # IMPLEMENTAR: Consultar tasa real del BCV
        #     # Por ahora devolvemos una tasa simulada
        #     tasa_simulada = 36.5314
            
        #     return {
        #         "code": "00",
        #         "fechavalor": fecha_valor,
        #         "tipocambio": tasa_simulada
        #     }
        # except Exception as e:
        #     logger.error(f"Error en consulta BCV: {str(e)}")
        #     return {
        #         "code": "01",
        #         "fechavalor": fecha_valor,
        #         "tipocambio": 0.0
        #     }
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
                
                # FALLBACK: Tasa de respaldo solo si falla el banco
                # try:
                #     tasa_respaldo = await _obtener_tasa_respaldo(moneda.upper())
                #     if tasa_respaldo > 0:
                #         logger.warning(f"Usando tasa de respaldo: {tasa_respaldo} VES/{moneda}")
                #         return {
                #             "code": "02",  # Código para tasa de respaldo
                #             "fechavalor": fecha_valor,
                #             "tipocambio": tasa_respaldo
                #         }
                # except Exception:
                #     pass
                
                # # Error final
                # return {
                #     "code": "01",
                #     "fechavalor": fecha_valor,
                #     "tipocambio": 0.0
                # }
            
        except Exception as e:
            logger.error(f"Error crítico en consulta BCV: {str(e)}")
            return {
                "code": "01",
                "fechavalor": fecha_valor,
                "tipocambio": 0.0
            }
    
    @staticmethod
    async def procesar_consulta_cliente(id_cliente: str, monto: str = None, telefono: str = None) -> Dict[str, Any]:
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
            from db import repository
            
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
        from db import repository
        print ("payload:", payload)
        referencia = payload.get("Referencia")
        # El cuerpo puede traer la bandera como "_verificacion" (alias) o ya normalizada como "verificacion"
        verificacion_flag = payload.get("verificacion", payload.get("_verificacion"))
        print("verificacion: ", verificacion_flag)
        hacer_verificacion = bool(verificacion_flag)
        #verifico filtros obligatorios si es hacer_verificacion=True
        print ("hacer_verificacion:", hacer_verificacion)
        # Si no se solicita verificación directa con el banco, usar solo Referencia.
        # Enviar cadenas vacías para no filtrar por esos campos.
        if not hacer_verificacion:
            filtros_sp = {
                "IdComercio": "",
                "TelefonoComercio": "",
                "TelefonoEmisor": "",
                "BancoEmisor": "",
                "Monto": "",
                "FechaHora": "",
                "Referencia": referencia or "",
            }
        else:
            filtros_sp = {
                "IdComercio": payload.get("IdComercio", ""),
                "TelefonoComercio": payload.get("TelefonoComercio", ""),
                "TelefonoEmisor": payload.get("TelefonoEmisor", ""),
                "BancoEmisor": payload.get("BancoEmisor", ""),
                "Monto": payload.get("Monto", ""),
                "FechaHora": payload.get("FechaHora", ""),
                "Referencia": referencia or "",
            }

        # Consulta en BD
        
        bd_result = await repository.consultar_notificacion_por_referencia(filtros_sp)
        print ("bd_result:", bd_result)
        fila_bd = bd_result.get("fila")
        ref_bd = fila_bd.get("Referencia") if fila_bd else None
        abono_bd = bool(fila_bd)

        code_banco = None
        reference_banco = None
        message_banco = None

        # Verificación directa con el banco si se solicita
        print ("Se hara verificacion en banco:", hacer_verificacion)
        if hacer_verificacion:
            try:
                #verifico campos obligatorios para consulta en banco
                if not all(payload.get(k) for k in ("TelefonoDestino", "Cedula", "Banco", "Monto")):
                    raise ValueError("Faltan campos obligatorios para verificación en banco")
                
                payload_banco = {
                    "TelefonoDestino": payload.get("TelefonoDestino") or payload.get("TelefonoEmisor"),
                    "Cedula": payload.get("Cedula"),
                    "Banco": payload.get("Banco") or payload.get("BancoEmisor"),
                    "Monto": payload.get("Monto")
                    # Concepto e Ip son opcionales y no obligatorios para verificación
                    #"Concepto": payload.get("Concepto"),
                    #"Ip": payload.get("Ip"),
                }

                # Solo llamamos si tenemos los campos mínimos
                if all(str(payload_banco.get(k) or '').strip() for k in ("TelefonoDestino", "Banco", "Monto", "Cedula")):
                    resp_banco = await R4Services.procesar_vuelto(payload_banco)
                    print("resp_banco:", resp_banco)
                    code_banco = resp_banco.get("code")
                    reference_banco = resp_banco.get("reference")
                    message_banco = resp_banco.get("message")
                else:
                    code_banco = "99"
                    message_banco = "Datos insuficientes para verificar en banco"
            except Exception as e:
                code_banco = "98"
                message_banco = f"Error verificando en banco: {str(e)}"

        coincide_referencia = bool(ref_bd and reference_banco and ref_bd == reference_banco)

        # Determinar código final
        if not abono_bd:
            code_final = "04"
            message_final = "No se encontró la referencia en BD"
            referencia_final = reference_banco or ref_bd or referencia
        else:
            if hacer_verificacion:
                if code_banco == "00" and coincide_referencia:
                    code_final = "00"
                    message_final = "Verificación exitosa en banco y BD"
                else:
                    code_final = code_banco or "06"
                    message_final = message_banco or "No coincide referencia o banco reportó error"
            else:
                code_final = "00"
                message_final = "Verificación exitosa en BD"
            referencia_final = reference_banco or ref_bd or referencia

        return {
            "code": code_final,
            "message": message_final,
            "reference": referencia_final,
            "abono_bd": abono_bd,
            "coincide_referencia": coincide_referencia,
            "code_banco": code_banco,
            "detalle_bd": fila_bd
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