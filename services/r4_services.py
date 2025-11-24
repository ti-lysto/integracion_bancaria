"""
SERVICIOS R4 - LÓGICA DE NEGOCIO
================================

Contiene la lógica específica para cada tipo de operación R4.
Cada método procesa un tipo diferente de transacción.

Creado por: Alicson Rubio
Fecha: Noviembre 2025
"""

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
            if Config.DEBUG:
                logger.info(f"Modo DEBUG: Usando tasa simulada para {moneda} - {fecha_valor}")
                return {
                    "code": "00",
                    "fechavalor": date.today().isoformat(),
                    "tipocambio": 236.5314
                }
            
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
                banco_url = "https://r4conecta.mibanco.com.ve/MBbcv"
                
                # Headers según especificación
                #from app.core.security import r4_security
                from core.auth import r4_authentication
                
                # Datos para HMAC según documento: "fechavalor + moneda"
                hmac_data = f"{fecha_valor}{moneda}"
                # Generar firma usando el consolidado `r4_authentication`.
                hmac_signature = r4_authentication.generate_response_signature({"data": hmac_data})
                # Antes: hmac_signature = r4_security.generate_response_signature({"data": hmac_data})
                
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
            cliente_valido = True
            
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