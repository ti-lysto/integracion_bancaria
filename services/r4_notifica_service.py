"""
SERVICIO R4 NOTIFICA - PROCESAMIENTO DE NOTIFICACIONES BANCARIAS
================================================================

¿QUÉ HACE ESTE ARCHIVO?
- Recibe las notificaciones que envían los bancos cuando alguien hace un pago móvil
- Valida que la información esté completa y correcta
- Guarda la notificación en la base de datos
- Responde al banco confirmando que se recibió la notificación

¿CUÁNDO SE USA?
- Automáticamente cuando un banco envía una notificación de pago
- El banco llama al endpoint /r4notifica de nuestra API
- Esto sucede cada vez que alguien hace un pago móvil a nuestro comercio

¿QUÉ INFORMACIÓN RECIBE?
- Datos del comercio que recibió el pago
- Datos de quien hizo el pago
- Monto, fecha, referencia del pago
- Información del banco

CREADO POR: Alicson Rubio
FECHA: Noviembre 2025
"""

import aiomysql
import logging
from typing import Dict, Any, Tuple, Optional
from core.config import get_database_config
#from core.security import validate_r4_notification, r4_security

# Configurar logging para registrar eventos importantes
logger = logging.getLogger(__name__)

class R4NotificaService:
    """
    CLASE PARA MANEJAR NOTIFICACIONES R4
    
    ¿Qué hace esta clase?
    - Se conecta a la base de datos MySQL
    - Llama al procedimiento almacenado para guardar notificaciones
    - Maneja errores de conexión y base de datos
    - Registra eventos en logs para monitoreo
    """
    
    def __init__(self):
        """
        INICIALIZAR EL SERVICIO
        
        ¿Qué hace?
        - Obtiene la configuración de la base de datos
        - Prepara el servicio para recibir notificaciones
        """
        self.db_config = get_database_config()
    
    async def procesar_notificacion(self, notification_data: Dict[str, Any], hmac_signature: Optional[str] = None) -> Dict[str, Any]:
        """
        PROCESAR UNA NOTIFICACIÓN DE PAGO
        
        ¿Qué hace?
        1. Valida que todos los datos obligatorios estén presentes
        2. Se conecta a la base de datos
        3. Llama al procedimiento almacenado para guardar la notificación
        4. Retorna el resultado (éxito o error)
        
        Parámetros:
        - notification_data: Diccionario con los datos del pago que envió el banco
        
        Retorna:
        - Diccionario con el resultado de la operación
        """
        try:
            # PASO 1: Validar seguridad R4 (merchant ID y HMAC)
            # Sanitizar referencia para logs (prevenir log injection)
            referencia = str(notification_data.get('Referencia', 'N/A')).replace('\n', '').replace('\r', '')[:50]
            logger.info(f"Procesando notificación R4 - Referencia: {referencia}")
            
            security_validation = validate_r4_notification(notification_data, hmac_signature)
            if not security_validation["valid"]:
                logger.warning(f"Validación de seguridad fallida: {security_validation['error']}")
                return {
                    "success": False,
                    "message": security_validation["error"],
                    "code": -1
                }
            
            # PASO 2: Validar datos obligatorios
            validation_result = self._validar_datos_obligatorios(notification_data)
            if not validation_result["valido"]:
                logger.warning(f"Datos inválidos en notificación: {validation_result['mensaje']}")
                return {
                    "success": False,
                    "message": validation_result["mensaje"],
                    "code": -1
                }
            
            # PASO 3: Guardar en base de datos
            result = await self._guardar_en_base_datos(notification_data)
            
            if result["codigo"] == 1:
                # PASO 4: Procesar abono al cliente final (según documento del banco)
                abono_result = await self._procesar_abono_cliente_final(notification_data)
                
                if abono_result["success"]:
                    logger.info(f"Notificación y abono procesados exitosamente - Referencia: {notification_data['Referencia']}")
                    return {
                        "success": True,
                        "message": "Notificación procesada y abono realizado",
                        "code": result["codigo"]
                    }
                else:
                    logger.error(f"Error en abono al cliente final: {abono_result['message']}")
                    return {
                        "success": False,
                        "message": f"Notificación guardada pero error en abono: {abono_result['message']}",
                        "code": -1
                    }
            elif result["codigo"] == 0:
                logger.info(f"Notificación duplicada - Referencia: {notification_data['Referencia']}")
                return {
                    "success": True,
                    "message": result["mensaje"],
                    "code": result["codigo"]
                }
            else:
                logger.error(f"Error guardando notificación: {result['mensaje']}")
                return {
                    "success": False,
                    "message": result["mensaje"],
                    "code": result["codigo"]
                }
                
        except Exception as e:
            logger.error(f"Error inesperado procesando notificación: {str(e)}")
            return {
                "success": False,
                "message": f"Error interno del servidor: {str(e)}",
                "code": -1
            }
    
    def _validar_datos_obligatorios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        VALIDAR QUE TODOS LOS DATOS OBLIGATORIOS ESTÉN PRESENTES
        
        ¿Qué valida?
        - Que todos los campos requeridos por R4 estén presentes
        - Que no estén vacíos o nulos
        - Que tengan el formato básico correcto
        
        Campos obligatorios según documentación R4:
        - IdComercio, TelefonoComercio, TelefonoEmisor
        - BancoEmisor, Monto, FechaHora, Referencia, CodigoRed
        """
        campos_obligatorios = [
            "IdComercio", "TelefonoComercio", "TelefonoEmisor",
            "BancoEmisor", "Monto", "FechaHora", "Referencia", "CodigoRed"
        ]
        
        for campo in campos_obligatorios:
            if campo not in data or not data[campo] or str(data[campo]).strip() == "":
                return {
                    "valido": False,
                    "mensaje": f"Campo obligatorio faltante o vacío: {campo}"
                }
        
        return {"valido": True, "mensaje": "Datos válidos"}
    
    # async def _guardar_en_base_datos(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     GUARDAR LA NOTIFICACIÓN EN LA BASE DE DATOS
        
    #     ¿Qué hace?
    #     1. Se conecta a MySQL
    #     2. Llama al stored procedure sp_guardar_notificacion_r4
    #     3. Pasa todos los parámetros de la notificación
    #     4. Obtiene el resultado (éxito, error o duplicado)
    #     5. Cierra la conexión
    #     """
    #     connection = None
    #     try:
    #         # Conectar a la base de datos
    #         connection = await aiomysql.connect(**self.db_config)
    #         cursor = await connection.cursor()
            
    #         # Llamar al stored procedure
    #         await cursor.callproc('sp_guardar_notificacion_r4', [
    #             data["IdComercio"],
    #             data["TelefonoComercio"], 
    #             data["TelefonoEmisor"],
    #             data.get("Concepto", ""),  # Campo opcional
    #             data["BancoEmisor"],
    #             data["Monto"],
    #             data["FechaHora"],
    #             data["Referencia"],
    #             data["CodigoRed"],
    #             "",  # p_mensaje (OUT parameter)
    #             0    # p_codigo (OUT parameter)
    #         ])
            
    #         # Obtener los parámetros de salida
    #         try:
    #             await cursor.execute("SELECT @_sp_guardar_notificacion_r4_9, @_sp_guardar_notificacion_r4_10")
    #             result = await cursor.fetchone()
    #         except Exception as e:
    #             logger.error(f"Error obteniendo parámetros de salida: {str(e)}")
    #             return {
    #                 "mensaje": "Error ejecutando procedimiento almacenado",
    #                 "codigo": -1
    #             }
            
    #         return {
    #             "mensaje": result[0] if result else "Error desconocido",
    #             "codigo": result[1] if result else -1
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Error de base de datos: {str(e)}")
    #         return {
    #             "mensaje": f"Error de base de datos: {str(e)}",
    #             "codigo": -1
    #         }
    #     finally:
    #         if connection:
    #             try:
    #                 await connection.ensure_closed()
    #             except Exception as e:
    #                 logger.error(f"Error cerrando conexión: {str(e)}")
    
    async def _guardar_en_base_datos(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        GUARDAR LA NOTIFICACIÓN EN LA BASE DE DATOS
        
        ¿Qué hace?
        1. Se conecta a MySQL
        2. Llama al stored procedure sp_guardar_notificacion_r4
        3. Pasa todos los parámetros de la notificación
        4. Obtiene el resultado (éxito, error o duplicado)
        5. Cierra la conexión
        """
        
        try:
            # Conectar a la base de datos
            resultado = await self._ejecutar_sp_generico(
                sp_nombre='sp_guardar_notificacion_r4',
                parametros_in=(
                    data["IdComercio"],
                    data["TelefonoComercio"], 
                    data["TelefonoEmisor"],
                    data.get("Concepto", ""),  # Campo opcional
                    data["BancoEmisor"],
                    data["Monto"],
                    data["FechaHora"],
                    data["Referencia"],
                    data["CodigoRed"]
                ),
                parametros_out=('p_mensaje', 'p_codigo')  # Nombres de los parámetros OUT
            )
            
            if resultado['exito']:
                # Procesar resultado
                mensaje = resultado['parametros_out'].get('p_mensaje', '')
                codigo = resultado['parametros_out'].get('p_codigo', -1)
                
                return {
                    "mensaje": mensaje,
                    "codigo": codigo,
                    "exito": True
                }
            else:
                return {
                    "mensaje": f"Error en base de datos: {resultado.get('error', 'Error desconocido')}",
                    "codigo": -1,
                    "exito": False
                }
            
        except Exception as e:
            print(f"Error guardando en base de datos: {str(e)}")
            return {
                "mensaje": f"Error: {str(e)}",
                "codigo": -1,
                "exito": False
            }

    async def _ejecutar_sp_generico(self, sp_nombre: str, parametros_in: Tuple[Any, ...] | None = None, parametros_out: Tuple[Any, ...] | None = None) -> Dict[str, Any]:
        """
        EJECUTAR UN STORED PROCEDURE GENÉRICO
        
        ¿Qué hace?
        - Se conecta a la base de datos
        - Llama al stored procedure con los parámetros dados
        - Retorna los resultados
        
        Parámetros:
        - sp_nombre: Nombre del stored procedure
        - parametros_in: Tupla con los nombres de los parámetros de entrada (opcional) debe incluir los paraámetros IN y OUT
        - parametros_out: Tupla con los nombres de los parámetros de salida (opcional) nombrar los parametros de salida como 
            tupla solo para recuperacion de parametros OUT
        
        Retorna:
        - Diccionario con los resultados del SP
        """
        connection = None
        try:
            connection = await aiomysql.connect(**self.db_config)
            cursor = await connection.cursor()
            
            # await cursor.callproc(sp_nombre, parametros_in )
            # resultados = await cursor.fetchall()
            
            # return resultados

            # Llamar al SP solo con parámetros de entrada
            await cursor.callproc(sp_nombre, parametros_in or ())

            # Obtener todos los resultados
            resultados = await cursor.fetchall()

            # Avanzar por todos los result sets
            while await cursor.nextset():
                pass

            # Si hay OUT, recuperarlos desde variables del servidor
            # Ejemplo: SELECT @_out1, @_out2, ...
            if len(parametros_out) > 0:
                out_vars = ", ".join(parametros_out) # Construir consulta SELECT
                await cursor.execute(f"SELECT {out_vars}") # Ejecutar consulta para obtener OUT
                out_values = await cursor.fetchone() # Obtener valores OUT
                # Agregar valores OUT al resultado si es necesario
                resultados += out_values
                # Procesar out_values si es necesario

            return resultados
            
        except Exception as e:
            logger.error(f"Error ejecutando SP {sp_nombre}: {str(e)}")
            return ()
        finally:
            if connection:
                try:
                    await connection.ensure_closed()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {str(e)}")

    async def _procesar_abono_cliente_final(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PROCESAR ABONO AL CLIENTE FINAL
        
        Según documento del banco:
        "El cliente debe validar dentro de su desarrollo los datos notificados, 
        para ello es necesario que realice un proceso de verificación de referencia, 
        banco y monto antes de abonar al cliente final."
        
        Esta función implementa la lógica de abono después de validar los datos.
        """
        
        try:
            id_comercio = notification_data.get("IdComercio")
            monto = notification_data.get("Monto")
            referencia = notification_data.get("Referencia")
            telefono_comercio = notification_data.get("TelefonoComercio")
            
            logger.info(f"Procesando abono al cliente final - Comercio: {id_comercio}, Monto: {monto}")
            
            # IMPLEMENTAR SEGÚN TU LÓGICA DE NEGOCIO:
            # 1. Identificar al cliente final basado en IdComercio/TelefonoComercio
            # 2. Validar que el cliente existe y está activo
            # 3. Procesar el abono (actualizar saldo, crear transacción, etc.)
            # 4. Generar comprobante o notificación al cliente
            
            cliente_info = await self._obtener_info_cliente(id_comercio, telefono_comercio)
            
            if not cliente_info:
                return {
                    "success": False,
                    "message": f"Cliente no encontrado: {id_comercio}"
                }
            
            # Procesar el abono
            abono_exitoso = await self._ejecutar_abono(
                cliente_info["id"],
                float(monto),
                referencia,
                notification_data
            )
            
            if abono_exitoso:
                logger.info(f"Abono exitoso al cliente {id_comercio} por {monto}")
                return {
                    "success": True,
                    "message": "Abono procesado exitosamente"
                }
            else:
                return {
                    "success": False,
                    "message": "Error procesando abono"
                }
                
        except Exception as e:
            logger.error(f"Error en abono al cliente final: {str(e)}")
            return {
                "success": False,
                "message": f"Error técnico en abono: {str(e)}"
            }
    
    async def _obtener_info_cliente(self, id_comercio: str, telefono: str) -> Dict[str, Any]:
        """
        OBTENER INFORMACIÓN DEL CLIENTE PARA EL ABONO
               
        - Obtener información necesaria para el abono en el log.
        """
        
        try:
            # EJEMPLO DE IMPLEMENTACIÓN:
            # Aquí consultarías tu base de datos de clientes
            
            # Por ahora, simulamos un cliente válido
            # CAMBIAR ESTA LÓGICA SEGÚN TU ESQUEMA DE BD
            
            if id_comercio and telefono:
                return {
                    "id": id_comercio,
                    "telefono": telefono,
                    "activo": True,
                    "nombre": f"Cliente {id_comercio}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo info del cliente: {str(e)}")
            return None
    
    # async def _ejecutar_abono(self, cliente_id: str, monto: float, referencia: str, datos_completos: Dict[str, Any]) -> bool:
    #     """
    #     EJECUTAR EL ABONO AL CLIENTE
                
    #     """
        
    #     try:
    #         logger.info(f"Ejecutando abono: Cliente {cliente_id}, Monto {monto}, Ref {referencia}")
            
    #         # IMPLEMENTAR SEGÚN TUS NECESIDADES:
    #         # 1. ACTUALIZAR SALDO DEL CLIENTE
    #         # await self._actualizar_saldo_cliente(cliente_id, monto)
            
    #         # 2. CREAR REGISTRO DE TRANSACCIÓN
    #         # await self._crear_transaccion_abono(cliente_id, monto, referencia, datos_completos)
            
    #         # 3. GENERAR COMPROBANTE
    #         # await self._generar_comprobante(cliente_id, monto, referencia)
            
    #         # 4. NOTIFICAR AL CLIENTE (SMS, email, push, etc.)
    #         # await self._notificar_cliente(cliente_id, monto, referencia)
            
    #         # Por ahora, simulamos éxito
    #         # IMPLEMENTAR SEGÚN TUS NECESIDADES
            
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Error ejecutando abono: {str(e)}")
    #         return False

# Instancia global del servicio
r4_service = R4NotificaService()