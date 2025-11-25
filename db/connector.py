"""
CONECTOR DE BASE DE DATOS PARA LA API R4 CONECTA
================================================

Este archivo maneja todas las conexiones a la base de datos MySQL.
Es como el "puente" entre nuestra aplicación Python y la base de datos.

¿Qué hace este archivo?
- Establece conexiones seguras a MySQL
- Maneja un pool de conexiones para mejor rendimiento
- Ejecuta procedimientos almacenados de forma segura
- Maneja errores de conexión y timeouts
- Cierra conexiones correctamente para evitar memory leaks

¿Qué es un pool de conexiones?
- Un conjunto de conexiones a la BD que se reutilizan
- Evita crear/cerrar conexiones constantemente (más rápido)
- Controla el número máximo de conexiones simultáneas
- Maneja automáticamente conexiones perdidas o expiradas

Creado por: Alicson Rubio
Fecha: 11/2025
"""

# IMPORTACIONES NECESARIAS
# ========================
import aiomysql
# aiomysql: Biblioteca para conectar a MySQL de forma asíncrona
# Permite que la aplicación no se "congele" mientras espera la BD

from typing import List, Tuple, Any, Optional, Dict
# List: Para listas
# Tuple: Para tuplas (datos inmutables)
# Any: Para cualquier tipo de dato
# Optional: Para valores que pueden ser None

import logging
# logging: Para registrar eventos y errores

from core.config import Config, get_database_config
# config: Configuración de la aplicación (credenciales de BD, etc.)


# CONFIGURACIÓN DE LOGGING
# ========================
# Creamos un logger específico para este módulo
logger = logging.getLogger(__name__)


# VARIABLE GLOBAL PARA EL POOL DE CONEXIONES
# ==========================================
# Esta variable guardará nuestro pool de conexiones
# Se inicializa la primera vez que se usa
_connection_pool: Optional[aiomysql.Pool] = None


# FUNCIÓN PARA OBTENER EL POOL DE CONEXIONES
# ==========================================
async def get_connection_pool() -> aiomysql.Pool:
    """
    OBTIENE O CREA EL POOL DE CONEXIONES A LA BASE DE DATOS
    
    ¿Qué hace esta función?
    - Si ya existe un pool, lo devuelve
    - Si no existe, crea uno nuevo con la configuración
    - Maneja errores de conexión
    - Configura parámetros óptimos para el pool
    
    ¿Qué es un pool de conexiones?
    - Un conjunto de conexiones pre-establecidas a la BD
    - Se reutilizan en lugar de crear nuevas cada vez
    - Mejora significativamente el rendimiento
    - Controla el uso de recursos del servidor
    
    Configuración del pool:
    - minsize: Número mínimo de conexiones siempre abiertas
    - maxsize: Número máximo de conexiones simultáneas
    - autocommit: Confirma automáticamente las transacciones
    
    Retorna:
    - Pool de conexiones listo para usar
    
    Errores posibles:
    - Error de conexión: Credenciales incorrectas, BD no disponible
    - Error de configuración: Parámetros inválidos
    - Error de red: Problemas de conectividad
        
    """
    
    # Usamos la variable global para mantener el pool
    global _connection_pool
    
    # Si ya tenemos un pool, lo devolvemos
    if _connection_pool is not None:
        return _connection_pool
    
    try:
        # CREAR NUEVO POOL DE CONEXIONES
        # ==============================
        logger.info("Creando nuevo pool de conexiones a MySQL...")
        
        db_config = get_database_config()
        
        _connection_pool = await aiomysql.create_pool(
            # CONFIGURACIÓN DE CONEXIÓN
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            db=db_config["db"],
            
            
            # # CONFIGURACIÓN DEL POOL
            # trasladado al config
            # minsize=1,  # Mínimo de conexiones
            # maxsize=10,  # Máximo de conexiones
             minsize=Config.DB_POOL_MIN_SIZE,  # Mínimo de conexiones
             maxsize=Config.DB_POOL_MAX_SIZE,  # Máximo de conexiones
            
            # CONFIGURACIÓN DE COMPORTAMIENTO
            autocommit=db_config["autocommit"],
            charset=db_config["charset"],
            
            # CONFIGURACIÓN DE TIMEOUTS
            connect_timeout=db_config["connect_timeout"]
        )
        
        logger.info(f"Pool de conexiones creado exitosamente. Min: {Config.DB_POOL_MIN_SIZE}, Max: {Config.DB_POOL_MAX_SIZE}")
        return _connection_pool
        
    except Exception as e:
        # Si hay error, lo registramos y re-lanzamos
        logger.error(f"Error creando pool de conexiones: {str(e)}")
        logger.error(f"Configuración: host={Config.DB_HOST}, port={Config.DB_PORT}, user={Config.DB_USER}, db={Config.DB_NAME}")
        raise


# FUNCIÓN PARA CERRAR EL POOL DE CONEXIONES
# =========================================
async def close_connection_pool():
    """
    CIERRA EL POOL DE CONEXIONES DE FORMA SEGURA
    
    ¿Cuándo se usa?
    - Al cerrar la aplicación
    - Para liberar recursos del servidor
    - En casos de emergencia o mantenimiento
    
    ¿Por qué es importante?
    - Evita memory leaks
    - Libera conexiones en el servidor MySQL
    - Permite un cierre limpio de la aplicación
    
    Proceso:
    1. Verifica que el pool exista
    2. Cierra todas las conexiones activas
    3. Espera a que terminen las operaciones pendientes
    4. Libera los recursos
    """
    
    global _connection_pool
    try:
        # Verificar si el pool existe
        
        if _connection_pool is not None:
            logger.info("Cerrando pool de conexiones...")
            
            # Cerrar el pool de forma segura (API aiomysql)
            _connection_pool.close()
            await _connection_pool.wait_closed()
            
            # Limpiar la variable global
            _connection_pool = None
            
            logger.info("Pool de conexiones cerrado exitosamente")
    except Exception as e:
        logger.error(f"Error cerrando pool de conexiones: {str(e)}")


# FUNCIÓN PRINCIPAL PARA EJECUTAR PROCEDIMIENTOS ALMACENADOS
# ==========================================================

async def ejecutar_sp_generico(
        #self, 
        sp_nombre: str, 
        parametros_in: Optional[Tuple[Any, ...]] = None,
        parametros_out: Optional[Tuple[str, ...]] = None,
        connection: Optional[aiomysql.Connection] = None
    ) -> Dict[str, Any]:
        """
        EJECUTAR UN STORED PROCEDURE GENÉRICO
        
        Parámetros:
        - sp_nombre: Nombre del stored procedure
        - parametros_in: Tupla con los valores de los parámetros de entrada (IN/INOUT)
        - parametros_out: Tupla con los nombres de los parámetros de salida (sin @)
        
        Retorna:
        - Diccionario con:
            * 'resultados': Lista de resultados de SELECT (si hay múltiples result sets)
            * 'parametros_out': Diccionario con valores de parámetros OUT
            * 'filas_afectadas': Número de filas afectadas
        """
        own_conn=False
        pool = None
        cursor = None
        try:
            if connection is None:
                own_conn = True
                pool = await get_connection_pool()
                connection = await pool.acquire()
            cursor = await connection.cursor()
            
            # Preparar parámetros para callproc
            # Si hay parámetros OUT, necesitamos crear marcadores de posición
            total_parametros = []
            
            if parametros_in:
                total_parametros.extend(parametros_in)
            
            # Agregar marcador de posición para parámetros OUT
            if parametros_out:
                # Para callproc, los parámetros OUT se pasan como None
                total_parametros.extend([None] * len(parametros_out))
            
            # Llamar al stored procedure
            if total_parametros:
                await cursor.callproc(sp_nombre, total_parametros)
            else:
                await cursor.callproc(sp_nombre)
            
            # Obtener todos los result sets (SELECT statements)
            resultados = []
            primer_resultado = await cursor.fetchall()
            if primer_resultado:
                resultados.append(primer_resultado)
            
            # Procesar múltiples result sets
            while await cursor.nextset():
                try:
                    result_set = await cursor.fetchall()
                    if result_set:
                        resultados.append(result_set)
                except aiomysql.ProgrammingError:
                    # No hay más result sets
                    break
            
            # Obtener filas afectadas (para INSERT, UPDATE, DELETE)
            filas_afectadas = cursor.rowcount
            
            # Recuperar parámetros OUT si existen
            valores_out = {}
            if parametros_out:
                # MySQL asigna variables @_sp_nombre_index
                base_idx = len(parametros_in) if parametros_in else 0
                selects = []
                for i, nombre in enumerate(parametros_out):
                    mysql_var = f"@_{sp_nombre}_{base_idx + i}"
                    selects.append(f"{mysql_var} AS {nombre}")
                if selects:
                    await cursor.execute(f"SELECT {', '.join(selects)}")
                    out_row = await cursor.fetchone()
                    if out_row:
                        for i, nombre in enumerate(parametros_out):
                            valores_out[nombre] = out_row[i]

            return {
                "exito": True,
                "sp": sp_nombre,
                "resultados": resultados,
                "parametros_out": valores_out,
                "filas_afectadas": filas_afectadas,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error ejecutando SP {sp_nombre}: {e}")
            return {
                "exito": False,
                "sp": sp_nombre,
                "resultados": [],
                "parametros_out": {},
                "filas_afectadas": 0,
                "error": str(e)
            }
        finally:
            if cursor:
                try:
                    await cursor.close()
                except Exception:
                    pass
            if own_conn and connection:
                try:
                    if pool is not None:
                        pool.release(connection)
                    else:
                        connection.close()
                except Exception:
                    pass

# async def call_stored_procedure(proc_name: str, params: List[Any]) -> Tuple[List[Any], List[Any]]:
#     """
#     EJECUTA UN PROCEDIMIENTO ALMACENADO EN LA BASE DE DATOS
    
#     ¿Qué hace esta función?
#     - Obtiene una conexión del pool
#     - Prepara la llamada al procedimiento almacenado
#     - Ejecuta el SP con los parámetros proporcionados
#     - Procesa los resultados y parámetros de salida
#     - Devuelve los datos de forma estructurada
#     - Maneja errores y libera la conexión
    
#     ¿Qué es un procedimiento almacenado?
#     - Código SQL que vive dentro de la base de datos
#     - Se ejecuta más rápido que SQL dinámico
#     - Puede recibir parámetros y devolver resultados
#     - Maneja lógica compleja y transacciones
    
#     Proceso paso a paso:
#     1. Obtiene conexión del pool
#     2. Crea cursor para ejecutar comandos
#     3. Prepara la llamada al SP con parámetros
#     4. Ejecuta el procedimiento almacenado
#     5. Obtiene todos los resultados (resultsets)
#     6. Obtiene parámetros de salida (OUT parameters)
#     7. Cierra cursor y devuelve conexión al pool
#     8. Devuelve resultados estructurados
    
#     Parámetros:
#     - proc_name: Nombre del procedimiento almacenado (ej: "sp_guardar_transaccion_r4")
#     - params: Lista de parámetros para el SP (IN, OUT, INOUT)
    
#     Retorna:
#     - Tupla con dos elementos:
#       * Lista de resultsets (tablas de datos que devuelve el SP)
#       * Lista de parámetros de salida (valores OUT del SP)
    
#     Ejemplo de uso:
#     ```python
#     resultsets, out_params = await call_stored_procedure(
#         "sp_guardar_transaccion_r4",
#         ["123", 100.50, "USD", "V12345678", "", 0]
#     )
#     print(f"Mensaje: {out_params[4]}")  # Parámetro OUT mensaje
#     print(f"Código: {out_params[5]}")   # Parámetro OUT código
#     ```
    
#     Manejo de errores:
#     - Errores de conexión: Pool no disponible, BD caída
#     - Errores de SP: Procedimiento no existe, parámetros incorrectos
#     - Errores de datos: Tipos incompatibles, valores inválidos
#     - Todos los errores se registran en logs antes de re-lanzarse
    
#     IMPORTANTE PARA MAÑANA:
#     - Los nombres de SP deben coincidir exactamente
#     - El número y orden de parámetros debe ser correcto
#     - Los tipos de datos deben ser compatibles
#     - Probar cada SP individualmente antes de usar en la API
#     """
    
#     # Obtener conexión del pool
#     pool = await get_connection_pool()
#     connection = None
#     cursor = None
    
#     try:
#         # PASO 1: OBTENER CONEXIÓN
#         # ========================
#         logger.debug(f"Obteniendo conexión del pool para SP: {proc_name}")
#         connection = await pool.acquire()
        
#         # PASO 2: CREAR CURSOR
#         # ===================
#         # El cursor es como un "puntero" que nos permite ejecutar comandos SQL
#         cursor = await connection.cursor()
        
#         # PASO 3: PREPARAR LLAMADA AL SP
#         # ==============================
#         # Para sp_guardar_notificacion_r4 que tiene parámetros OUT
        
#         if proc_name == "sp_guardar_notificacion_r4":
#             # Llamada especial para este SP con parámetros OUT
#             placeholders = ', '.join(['%s'] * len(params))
#             call_statement = f"CALL {proc_name}({placeholders}, @p_mensaje, @p_codigo)"
#         else:
#             # Llamada genérica para otros SPs
#             placeholders = ', '.join(['%s'] * len(params))
#             call_statement = f"CALL {proc_name}({placeholders})"
        
#         logger.debug(f"Ejecutando: {call_statement}")
#         logger.debug(f"Parámetros: {params}")
        
#         # PASO 4: EJECUTAR PROCEDIMIENTO ALMACENADO
#         # =========================================
#         await cursor.execute(call_statement, params)
        
#         # PASO 5: OBTENER RESULTSETS
#         # ==========================
#         # Un SP puede devolver múltiples conjuntos de resultados (tablas)
#         resultsets = []
        
#         # Obtener el primer resultset
#         if cursor.description:  # Si hay columnas en el resultado
#             resultset = await cursor.fetchall()
#             resultsets.append(resultset)
        
#         # Obtener resultsets adicionales (si los hay)
#         while await cursor.nextset():
#             if cursor.description:
#                 resultset = await cursor.fetchall()
#                 resultsets.append(resultset)
        
#         # PASO 6: OBTENER PARÁMETROS DE SALIDA
#         # ====================================
#         # Los parámetros OUT se obtienen con una consulta separada
#         # Según tu SP: OUT p_mensaje VARCHAR(500), OUT p_codigo INT
        
#         try:
#             # Consultar los parámetros OUT usando variables de sesión
#             await cursor.execute("SELECT @p_mensaje, @p_codigo")
#             out_result = await cursor.fetchone()
            
#             if out_result:
#                 out_params = list(out_result)  # [mensaje, codigo]
#             else:
#                 out_params = ["", 0]  # Valores por defecto
                
#         except Exception as out_error:
#             logger.warning(f"No se pudieron obtener parámetros OUT: {out_error}")
#             out_params = ["", 0]  # Valores por defecto si falla
        
#         logger.debug(f"SP ejecutado exitosamente. Resultsets: {len(resultsets)}, Out params: {len(out_params)}")
        
#         return resultsets, out_params
        
#     except Exception as e:
#         # MANEJO DE ERRORES
#         # ================
#         logger.error(f"Error ejecutando SP {proc_name}: {str(e)}")
#         logger.error(f"Parámetros: {params}")
        
#         # Re-lanzar el error para que lo maneje el código que llama
#         raise
        
#     finally:
#         # LIMPIEZA DE RECURSOS
#         # ===================
#         # Siempre cerrar cursor y devolver conexión al pool
        
#         if cursor:
#             await cursor.close()
#             logger.debug("Cursor cerrado")
        
#         if connection:
#             # Devolver conexión al pool (no cerrarla)
#             pool.release(connection)
#             logger.debug("Conexión devuelta al pool")


# FUNCIONES DE UTILIDAD PARA DEBUGGING
# ====================================

async def test_connection() -> bool:
    """
    PRUEBA LA CONEXIÓN A LA BASE DE DATOS
    
    ¿Para qué sirve?
    - Verificar que la configuración sea correcta
    - Probar conectividad antes de usar la aplicación
    - Debugging de problemas de conexión
    
    Retorna:
    - True si la conexión es exitosa
    - False si hay problemas
    
    Uso recomendado:
    - Ejecutar al iniciar la aplicación
    - Incluir en health checks
    - Usar para debugging
    """
    
    try:
        logger.info("Probando conexión a la base de datos...")
        
        # Obtener pool y conexión
        pool = await get_connection_pool()
        connection = await pool.acquire()
        
        # Ejecutar consulta simple
        cursor = await connection.cursor()
        await cursor.execute("SELECT 1 as test")
        result = await cursor.fetchone()
        
        # Limpiar recursos
        await cursor.close()
        pool.release(connection)
        
        # Verificar resultado
        if result and result[0] == 1:
            logger.info("Conexión a base de datos exitosa")
            return True
        else:
            logger.error("Conexión falló: resultado inesperado")
            return False
            
    except Exception as e:
        logger.error(f"Error probando conexión: {str(e)}")
        return False




async def get_pool_status() -> Dict[str, Any]:
    """
    OBTIENE INFORMACIÓN DEL ESTADO DEL POOL DE CONEXIONES
    
    ¿Para qué sirve?
    - Monitoreo del pool de conexiones
    - Debugging de problemas de rendimiento
    - Métricas para dashboards
    
    Retorna:
    - Diccionario con estadísticas del pool
    
    NOTA: Se implementará completamente mañana
    """
    
    global _connection_pool
    
    if _connection_pool is None:
        return {"status": "no_inicializado"}
    
    # Información básica del pool
    # En futuras versiones se pueden agregar más métricas
    return {
        "status": "activo",
        "minsize": 1,
        "maxsize": 10,
        "mensaje": "Pool funcionando correctamente"
    }


# INFORMACIÓN ADICIONAL SOBRE ESTE ARCHIVO
# ========================================
"""
PUNTOS IMPORTANTES SOBRE connector.py:

1. PATRÓN CONNECTION POOL:
   - Reutiliza conexiones en lugar de crear nuevas
   - Mejora significativamente el rendimiento
   - Controla el uso de recursos del servidor
   - Maneja automáticamente conexiones perdidas

2. PROGRAMACIÓN ASÍNCRONA:
   - Usa async/await para no bloquear la aplicación
   - Permite manejar múltiples peticiones simultáneamente
   - Mejor rendimiento

3. MANEJO DE ERRORES:
   - Registra todos los errores en logs
   - Libera recursos incluso si hay errores
   - Proporciona información útil para debugging

4. CONFIGURACIÓN FLEXIBLE:
   - Usa variables de entorno para configuración
   - Fácil cambiar parámetros sin modificar código
   - Diferentes configuraciones para desarrollo/producción

5. MEJORES PRÁCTICAS:
   - Siempre cerrar cursors y devolver conexiones
   - Usar try/finally para limpieza de recursos
   - Registrar eventos importantes en logs
   - Manejar timeouts y reconexiones


# Ver conexiones activas
SHOW PROCESSLIST;

# Ver estado de la base de datos
SHOW STATUS LIKE 'Connections';
```
"""