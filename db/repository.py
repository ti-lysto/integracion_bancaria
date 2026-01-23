"""
REPOSITORIO DE DATOS PARA LA API R4 CONECTA
===========================================

Este archivo maneja toda la comunicación con la base de datos.
Es como el "traductor" entre nuestra aplicación Python y la base de datos MySQL.

¿Qué hace este archivo?
- Se conecta a la base de datos MySQL
- Ejecuta procedimientos almacenados (stored procedures)
- Maneja parámetros de entrada y salida
- Procesa los resultados y los devuelve en formato Python
- Maneja errores de base de datos de forma segura

¿Por qué usar procedimientos almacenados?
- Mayor seguridad (previene inyección SQL)
- Mejor rendimiento (código compilado en la BD)
- Lógica de negocio centralizada en la base de datos
- Facilita el mantenimiento y auditoría
- Permite transacciones complejas

Creado por: Alicson Rubio
Fecha: 11/2025
"""

# IMPORTACIONES NECESARIAS
# ========================
from typing import Any, Dict, List, Tuple
# Any: Para cualquier tipo de dato
# Dict: Para diccionarios (clave-valor)
# List: Para listas
# Tuple: Para tuplas (datos inmutables)

#from app.db.connector import call_stored_procedure
# connector: Módulo que maneja las conexiones a la base de datos


# FUNCIÓN PRINCIPAL PARA GUARDAR TRANSACCIONES
# ============================================
async def guardar_transaccion_sp(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    GUARDA UNA TRANSACCIÓN DE R4 USANDO PROCEDIMIENTO ALMACENADO
    
    ¿Qué hace esta función?
    - Toma los datos de una transacción de R4
    - Los prepara en el formato que espera el procedimiento almacenado
    - Ejecuta el SP en la base de datos
    - Procesa los resultados y parámetros de salida
    - Devuelve una respuesta estructurada
    
    ¿Qué es un procedimiento almacenado (SP)?
    - Es código SQL que vive dentro de la base de datos
    - Se ejecuta más rápido que SQL dinámico
    - Puede tener parámetros de entrada (IN) y salida (OUT)
    - Puede devolver múltiples conjuntos de resultados
    - Maneja transacciones y lógica compleja
    
    ¿Por qué usar SP en lugar de SQL directo?
    - SEGURIDAD: Previene inyección SQL
    - RENDIMIENTO: Código precompilado en la BD
    - MANTENIMIENTO: Lógica centralizada
    - AUDITORÍA: Fácil seguimiento de cambios
    - TRANSACCIONES: Manejo automático de rollback
    
    Proceso paso a paso:
    1. Recibe los datos de la transacción
    2. Prepara los parámetros para el SP
    3. Llama al conector para ejecutar el SP
    4. Procesa los resultados
    5. Devuelve respuesta estructurada
    
    
    """
    
    # CONFIGURACIÓN DEL PROCEDIMIENTO ALMACENADO
    # ==========================================
    # Usamos el SP creado con la logica: sp_guardar_notificacion_r4
    proc_name = "sp_guardar_notificacion_r4"
    
    # PREPARACIÓN DE PARÁMETROS
    # ========================
    # Aquí preparamos los parámetros que enviamos al SP
    # El orden y tipo debe coincidir con la definición del SP
    
    # PARÁMETROS DE ENTRADA (IN) - Solo los parámetros IN
    # params: List[Any] = [
    #     datos.get("IdComercio", ""),           # Cédula del comercio
    #     datos.get("TelefonoComercio", ""),     # Teléfono del comercio  
    #     datos.get("TelefonoEmisor", ""),       # Teléfono del que pagó
    #     datos.get("Concepto", ""),             # Descripción del pago
    #     datos.get("BancoEmisor", ""),          # Código del banco
    #     datos.get("Monto", ""),                # Monto del pago
    #     datos.get("FechaHora", ""),            # Fecha y hora
    #     datos.get("Referencia", ""),           # Referencia única
    #     datos.get("CodigoRed", "")             # Código de respuesta
    # ]
    parametros_in = (
        datos.get("IdComercio", ""),           # Cédula del comercio
        datos.get("TelefonoComercio", ""),     # Teléfono del comercio  
        datos.get("TelefonoEmisor", ""),       # Teléfono del que pagó
        datos.get("Concepto", ""),             # Descripción del pago
        datos.get("BancoEmisor", ""),          # Código del banco
        datos.get("Monto", ""),                # Monto del pago
        datos.get("FechaHora", ""),            # Fecha y hora
        datos.get("Referencia", ""),           # Referencia única
        datos.get("CodigoRed", "")             # Código de respuesta
    )

    # EJECUCIÓN DEL PROCEDIMIENTO ALMACENADO
    # =====================================
    # Llamamos al conector que maneja la conexión y ejecución
    #resultsets, out_params = await call_stored_procedure(proc_name, params)
    parametros_out = ("p_mensaje", "p_codigo")
    
    # EJECUCIÓN DEL PROCEDIMIENTO ALMACENADO
    from db.connector import ejecutar_sp_generico
    resultado = await ejecutar_sp_generico(
        #None,  # self no es necesario si la función es independiente
        proc_name, 
        parametros_in, 
        parametros_out
    )

    # PROCESAMIENTO DE RESULTADOS
    # ===========================
    # Construimos una respuesta estructurada con toda la información
    # respuesta = {
    #     # Conjuntos de resultados que devuelve el SP (tablas de datos)
    #     "resultsets": resultsets,
        
    #     # Parámetros de salida del SP (mensajes, códigos, etc.)
    #     "out_params": out_params,
        
    #     # Información adicional para debugging
    #     "procedimiento": proc_name,
    #     "parametros_enviados": len(params),
    #     "exito": True  # Si llegamos aquí, no hubo errores
    # }
    respuesta = {
        "resultsets": resultado.get("resultados", []),
        "out_params": resultado.get("parametros_out", {}),
        "filas_afectadas": resultado.get("filas_afectadas", 0),
        "procedimiento": proc_name,
        "parametros_enviados": len(parametros_in),
        "exito": resultado.get("exito", False),
        "error": resultado.get("error", None)
    }
    
    return respuesta


# FUNCIONES AUXILIARES PARA FUTURAS EXPANSIONES
# =============================================

async def consultar_transaccion_sp(id_transaccion: str) -> Dict[str, Any]:
    """
    CONSULTA UNA TRANSACCIÓN ESPECÍFICA POR SU ID
    
    ¿Para qué sirve?
    - Buscar transacciones específicas
    - Verificar el estado de operaciones
    - Auditoría y seguimiento
    
    Esta función está preparada para futuras expansiones.
    Se implementará cuando sea necesario consultar transacciones específicas.
    
    Parámetros:
    - id_transaccion: ID único de la transacción a consultar
    
    Retorna:
    - Diccionario con los datos de la transacción
    - None si no se encuentra
    
    NOTA: Se implementará mañana junto con el SP correspondiente
    """
    
    # Nombre del SP para consultas (a crear mañana)
    proc_name = "sp_consultar_transaccion_r4"
    
    # Parámetros para la consulta
    params = [
        id_transaccion,  # ID a buscar
        "",              # Resultado (OUT)
        0                # Código (OUT)
    ]
    
    # Por ahora devolvemos estructura vacía
    # Se implementará completamente mañana
    return {
        "encontrada": False,
        "datos": None,
        "mensaje": "Función en desarrollo"
    }


async def actualizar_estado_transaccion_sp(id_transaccion: str, nuevo_estado: str) -> Dict[str, Any]:
    """
    ACTUALIZA EL ESTADO DE UNA TRANSACCIÓN
    
    ¿Para qué sirve?
    - Cambiar estados de transacciones (pendiente -> procesado)
    - Marcar operaciones como completadas o fallidas
    - Seguimiento del ciclo de vida de transacciones
    
    Esta función está preparada para futuras expansiones.
    
    Parámetros:
    - id_transaccion: ID de la transacción a actualizar
    - nuevo_estado: Estado nuevo ("procesado", "error", "cancelado", etc.)
    
    Retorna:
    - Diccionario con el resultado de la actualización
    
    NOTA: No implementado aun.
    """
    
    # Nombre del SP para actualizaciones (a crear mañana)
    proc_name = "sp_actualizar_estado_transaccion_r4"
    
    # Parámetros para la actualización
    params = [
        id_transaccion,  # ID a actualizar
        nuevo_estado,    # Nuevo estado
        "",              # Mensaje (OUT)
        0                # Código (OUT)
    ]
    
    # Por ahora devolvemos estructura vacía
    # Se implementará completamente mañana
    return {
        "actualizado": False,
        "mensaje": "Función en desarrollo"
    }


async def consultar_notificacion_por_referencia(filtros: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta notificación en BD usando sp_consulta_notificacion_r4.

    Parámetros esperados por el SP (IN):
    IdComercio, TelefonoComercio, TelefonoEmisor, BancoEmisor,
    Monto, FechaHora, Referencia.
    """

    proc_name = "sp_consulta_notificacion_r4"

    parametros_in = (
        filtros.get("IdComercio", ""),
        filtros.get("TelefonoComercio", ""),
        filtros.get("TelefonoEmisor", ""),
        filtros.get("BancoEmisor", ""),
        filtros.get("Monto", ""),
        filtros.get("FechaHora", ""),
        filtros.get("Referencia", ""),
    )

    from db.connector import ejecutar_sp_generico
    print ("Ejecutando SP:", proc_name, "con parámetros:", parametros_in)
    resultado = await ejecutar_sp_generico(
        proc_name,
        parametros_in,
        parametros_out=()
    )

    # Normalizar el primer resultset a una lista de dicts para evitar tuple.get()
    filas_raw = resultado.get("resultados", [])
    # Seleccionar el primer resultset no vacío
    primer_no_vacio = []
    for rs in filas_raw:
        if isinstance(rs, list) and rs:
            primer_no_vacio = rs
            break

    filas = []
    if primer_no_vacio and isinstance(primer_no_vacio, list):
        # El SP devuelve tuplas; las mapeamos a claves conocidas
        columnas_posibles = [
            "IdComercio",
            "TelefonoComercio",
            "TelefonoEmisor",
            "BancoEmisor",
            "Monto",
            "FechaHora",
            "Referencia",
        ]
        for tupla in primer_no_vacio:
            if isinstance(tupla, tuple):
                fila_dict = {}
                for idx, valor in enumerate(tupla):
                    clave = columnas_posibles[idx] if idx < len(columnas_posibles) else f"col{idx}"
                    fila_dict[clave] = valor
                filas.append(fila_dict)
            elif isinstance(tupla, dict):
                filas.append(tupla)

    fila = filas[0] if filas else None
    # Fallback: si el SP no devolvió filas, intentar consulta directa equivalente
    if not fila:
        try:
            from db.connector import get_connection_pool
            pool = await get_connection_pool()
            conn = await pool.acquire()
            cur = await conn.cursor()
            try:
                base_sql = "SELECT * FROM r4_notifications WHERE 1=1"
                where = []
                args = []
                if filtros.get("IdComercio"):
                    where.append(" AND IdComercio = %s")
                    args.append(filtros["IdComercio"])
                if filtros.get("TelefonoComercio"):
                    where.append(" AND TelefonoComercio = %s")
                    args.append(filtros["TelefonoComercio"])
                if filtros.get("TelefonoEmisor"):
                    where.append(" AND TelefonoEmisor = %s")
                    args.append(filtros["TelefonoEmisor"])
                if filtros.get("BancoEmisor"):
                    where.append(" AND BancoEmisor = %s")
                    args.append(filtros["BancoEmisor"])
                if filtros.get("Monto"):
                    where.append(" AND Monto = %s")
                    args.append(filtros["Monto"])
                if filtros.get("FechaHora"):
                    where.append(" AND FechaHora = %s")
                    args.append(filtros["FechaHora"])
                if filtros.get("Referencia"):
                    where.append(" AND Referencia = %s")
                    args.append(filtros["Referencia"])

                sql = base_sql + "".join(where) + " ORDER BY FechaHora DESC"
                await cur.execute(sql, tuple(args))
                direct_rows = await cur.fetchall()

                if direct_rows:
                    filas = []
                    columnas_posibles = [
                        "IdComercio",
                        "TelefonoComercio",
                        "TelefonoEmisor",
                        "BancoEmisor",
                        "Monto",
                        "FechaHora",
                        "Referencia",
                    ]
                    for tupla in direct_rows:
                        if isinstance(tupla, tuple):
                            fila_dict = {}
                            for idx, valor in enumerate(tupla):
                                clave = columnas_posibles[idx] if idx < len(columnas_posibles) else f"col{idx}"
                                fila_dict[clave] = valor
                            filas.append(fila_dict)
                        elif isinstance(tupla, dict):
                            filas.append(tupla)
                    fila = filas[0]
            finally:
                await cur.close()
                pool.release(conn)
        except Exception:
            pass

    return {
        "fila": fila,
        "filas": filas,
        "exito": resultado.get("exito", False),
        "error": resultado.get("error"),
        "procedimiento": proc_name,
    }


# FUNCIONES DE UTILIDAD PARA DEBUGGING
# ====================================

# def formatear_parametros_sp(params: List[Any]) -> str:
#     """
#     FORMATEA PARÁMETROS PARA LOGGING Y DEBUGGING
    
#     ¿Para qué sirve?
#     - Crear logs legibles de los parámetros enviados al SP
#     - Facilitar el debugging de problemas
#     - Auditoría de llamadas a procedimientos almacenados
    
#     Parámetros:
#     - params: Lista de parámetros del SP
    
#     Retorna:
#     - String formateado para logs
#     """
    
#     # Convertimos cada parámetro a string de forma segura
#     params_str = []
#     for i, param in enumerate(params):
#         if param is None:
#             params_str.append(f"P{i+1}: NULL")
#         elif isinstance(param, str):
#             # Truncamos strings muy largos para logs
#             param_truncado = param[:50] + "..." if len(param) > 50 else param
#             params_str.append(f"P{i+1}: '{param_truncado}'")
#         else:
#             params_str.append(f"P{i+1}: {param}")
    
#     return " | ".join(params_str)


# INFORMACIÓN ADICIONAL SOBRE ESTE ARCHIVO
# ========================================
"""
PUNTOS IMPORTANTES SOBRE repository.py:

1. PATRÓN REPOSITORY:
   - Abstrae el acceso a datos de la lógica de negocio
   - Facilita el testing 
   - Centraliza todas las operaciones de base de datos
   - Permite cambiar la BD sin afectar el resto del código

2. PROCEDIMIENTOS ALMACENADOS:
   - Más seguros que SQL dinámico
   - Mejor rendimiento 
   - Lógica de negocio en la BD
   - Facilita auditoría y control de cambios

3. MANEJO DE PARÁMETROS:
   - IN: Datos que enviamos al SP
   - OUT: Datos que el SP nos devuelve

4. ESTRUCTURA DE RESPUESTA:
   - resultsets: Tablas de datos que devuelve el SP
   - out_params: Parámetros de salida (mensajes, códigos)
   - Información adicional para debugging


"""