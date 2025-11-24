"""
CONFIGURACIÓN DE LA APLICACIÓN R4 CONECTA
=========================================

¿QUÉ ES ESTE ARCHIVO?
- Contiene toda la configuración de la aplicación centralizada
- No depende de archivos .env externos
- Configuración de base de datos, seguridad, logs, etc.

¿POR QUÉ ES IMPORTANTE?
- Centraliza toda la configuración en un solo lugar
- Elimina dependencias externas de configuración
- Simplifica el manejo de configuraciones

¿CÓMO SE USA?
- Las otras partes de la aplicación importan configuraciones desde aquí
- Todos los valores están definidos directamente en este archivo
- Ejemplo: get_database_config() retorna la configuración de BD

CREADO POR: Alicson Rubio
FECHA: Noviembre 2025
"""

import logging
import os
from typing import Dict, Any

# Cargar variables de entorno desde un archivo .env si existe
from dotenv import load_dotenv
load_dotenv()

class Config:
    """
    CLASE DE CONFIGURACIÓN PRINCIPAL
    
    ¿Qué contiene?
    - Configuración de base de datos
    - Configuración de seguridad
    - Configuración de logging
    - URLs y puertos
    """
    
    # =====================================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # =====================================================
    
    # Host de la base de datos (donde está instalado MySQL)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    
    # Puerto de MySQL (por defecto 3306)
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    
    # Nombre de la base de datos
    DB_NAME = os.getenv("DB_NAME", "LystoLocal") #"LystoLocal" / "Lysto"
    
    # Usuario de MySQL
    DB_USER = os.getenv("DB_USER", "root")
    
    # Contraseña de MySQL
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    
    # Mínimo de conexiones en el pool
    DB_POOL_MIN_SIZE = 1
    
    # Máximo de conexiones en el pool
    DB_POOL_MAX_SIZE = 10
    
    # =====================================================
    # CONFIGURACIÓN DE LA API
    # =====================================================
    
    # Puerto donde correrá la API
    API_PORT = 8000
    
    # Host de la API (0.0.0.0 para permitir conexiones externas)
    API_HOST = "0.0.0.0"
    
    # Modo debug (True para desarrollo, False para producción)
    DEBUG = os.getenv("DEBUG", "False") #True
    
    # =====================================================
    # CONFIGURACIÓN DE SEGURIDAD R4
    # =====================================================
    
    # ID del comercio en el sistema R4 (proporcionado por el banco)
    # Ahora se obtiene desde la variable de entorno R4_MERCHANT_ID o usa
    # un valor por defecto no válido para forzar la configuración en producción.
    R4_MERCHANT_ID = os.getenv("R4_MERCHANT_ID", "id_comercio")
    
    # Clave secreta para HMAC (proporcionada por el banco)
    # Se debe definir en la variable de entorno R4_SECRET_KEY. NO almacenar
    # esta clave en el código fuente.
    #R4_SECRET_KEY = os.getenv("R4_SECRET_KEY", "clave_secreta")
    R4_SECRET_KEY = R4_MERCHANT_ID#os.getenv("R4_MERCHANT_ID", "id_comercio")
    


    # Timeout para requests (en segundos)
    REQUEST_TIMEOUT = 30
    
    # IPs permitidas del banco (según documento R4 Conecta V3.0)
    BANCO_IPS_PERMITIDAS = os.getenv("BANCO_IPS_PERMITIDAS", "").split(",") 
    if DEBUG: BANCO_IPS_PERMITIDAS.append("127.0.0.1") # Añadir localhost en modo debug
    BANCO_IPS_PERMITIDAS = tuple(BANCO_IPS_PERMITIDAS) # Convertir a tupla para inmutabilidad

    
    # =====================================================
    # CONFIGURACIÓN DE LOGGING
    # =====================================================
    
    # Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = "INFO"
    
    # Archivo donde guardar logs
    LOG_FILE = "logs/r4_conecta.log"

def get_database_config() -> Dict[str, Any]:
    """
    OBTENER CONFIGURACIÓN DE BASE DE DATOS
    
    ¿Qué hace?
    - Retorna un diccionario con la configuración de MySQL
        
    ¿Cuándo se usa?
    - Al conectarse a la base de datos
    - En los servicios que necesitan acceso a BD
    
    Retorna:
    - Diccionario con host, port, user, password, db, etc.
    """
    return {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "db": Config.DB_NAME,
        "charset": "utf8mb4",
        "autocommit": True,
        "connect_timeout": 10 #,
        # "minsize": Config.DB_POOL_MIN_SIZE,
        # "maxsize": Config.DB_POOL_MAX_SIZE
    }

def get_api_config() -> Dict[str, Any]:
    """
    OBTENER CONFIGURACIÓN DE LA API
    
    ¿Qué incluye?
    - Host y puerto donde correrá la API
    - Configuraciones de desarrollo/producción
    - Timeouts y límites
    """
    return {
        "host": Config.API_HOST,
        "port": Config.API_PORT,
        "debug": Config.DEBUG,
        "reload": Config.DEBUG  # Auto-reload solo en desarrollo
    }

def get_r4_config() -> Dict[str, Any]:
    """
    OBTENER CONFIGURACIÓN ESPECÍFICA DE R4
    
    ¿Qué incluye?
    - Clave secreta para autenticación HMAC
    - Timeouts para comunicación con bancos
    - Configuraciones de seguridad
    """
    #print(Config.R4_MERCHANT_ID)
    return {
        "merchant_id": Config.R4_MERCHANT_ID,
        "secret_key": Config.R4_SECRET_KEY,
        "timeout": Config.REQUEST_TIMEOUT,
        "allowed_ips": Config.BANCO_IPS_PERMITIDAS
    }

def setup_logging():
    """
    CONFIGURAR EL SISTEMA DE LOGS
    
    ¿Qué hace?
    - Configura el formato de los logs
    - Define dónde se guardan los logs
    - Establece el nivel de logging
    
    ¿Por qué es importante?
    - Permite monitorear la aplicación
    - Ayuda a detectar errores y problemas
    - Registra todas las transacciones importantes
    """
    if Config.DEBUG:
        # Crear directorio de logs si no existe
        try:
            log_dir = os.path.dirname(Config.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Advertencia: No se pudo crear directorio de logs: {e}")
            Config.LOG_FILE = "r4_conecta.log"  # Fallback al directorio actual
    

        # Configurar formato de logs
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Configurar logging con manejo de errores
        try:
            # Intentar configuración completa con archivo
            logging.basicConfig(
                level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
                format=log_format,
                handlers=[
                    # Guardar en archivo
                    logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
                    # Mostrar en consola
                    logging.StreamHandler()
                ]
            )
        except (OSError, PermissionError) as e:
            # Fallback: solo consola si no se puede escribir archivo
            print(f"Advertencia: No se pudo configurar archivo de log: {e}")
            logging.basicConfig(
                level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
                format=log_format,
                handlers=[logging.StreamHandler()]
            )
        
        # Log inicial
        logger = logging.getLogger(__name__)
        logger.info("Sistema de logging configurado correctamente")
        logger.info(f"Nivel de logging: {Config.LOG_LEVEL}")
        logger.info(f"Archivo de logs: {Config.LOG_FILE}")
    else: pass

def validate_config():
    """
    VALIDAR QUE LA CONFIGURACIÓN SEA CORRECTA
    
    ¿Qué valida?
    - Que las variables obligatorias estén definidas
    - Que los valores tengan formato correcto
    - Que se pueda conectar a la base de datos
    
    ¿Cuándo se usa?
    - Al iniciar la aplicación
    - Para detectar problemas de configuración temprano
    """
    
    logger = logging.getLogger(__name__)
    
    # Validar configuración de base de datos
    if not Config.DB_NAME:
        raise ValueError("DB_NAME no está configurado")
    
    if not Config.DB_USER:
        raise ValueError("DB_USER no está configurado")
    
    # Validar configuración R4
    if Config.R4_MERCHANT_ID == "id_comercio":
        logger.warning("R4_MERCHANT_ID usa valor por defecto - CAMBIAR EN PRODUCCIÓN")
    
    if Config.R4_SECRET_KEY == "clave_secreta":
        logger.warning("R4_SECRET_KEY usa valor por defecto - CAMBIAR EN PRODUCCIÓN")
    
    # Validar puertos
    if not (1 <= Config.API_PORT <= 65535):
        raise ValueError(f"API_PORT inválido: {Config.API_PORT}")
    
    if not (1 <= Config.DB_PORT <= 65535):
        raise ValueError(f"DB_PORT inválido: {Config.DB_PORT}")
    
    

    logger.info("Configuración validada correctamente")

# Configurar logging al importar el módulo
setup_logging()