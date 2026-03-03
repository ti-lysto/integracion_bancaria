

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
    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "") #"LystoLocal" / "Lysto"
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_POOL_MIN_SIZE = 1
    DB_POOL_MAX_SIZE = 10
    
    # =====================================================
    # CONFIGURACIÓN DE LA API
    # =====================================================
    API_VERSION = os.getenv("API_VERSION", "0.0.0")
    API_PORT = int(os.getenv("API_PORT", 0))
    API_HOST = "0.0.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes") #True
    
    # =====================================================
    # CONFIGURACIÓN DE SEGURIDAD R4
    # =====================================================
    R4_MERCHANT_ID = os.getenv("R4_MERCHANT_ID")
    R4_UUID = os.getenv("R4_UUID")
    R4_BANCO_URL = os.getenv("R4_BANCO_URL")
    REQUEST_TIMEOUT = 30
    BANCO_IPS_PERMITIDAS = [ip for ip in os.getenv("BANCO_IPS_PERMITIDAS", "").split(",") if ip]
    # Incluimos localhost para pruebas locales cuando no hay lista explícita o cuando DEBUG está activo.
    if DEBUG or not BANCO_IPS_PERMITIDAS:
        BANCO_IPS_PERMITIDAS.append("127.0.0.1")
    BANCO_IPS_PERMITIDAS = tuple(BANCO_IPS_PERMITIDAS) # Convertir a tupla para inmutabilidad
    R4_REINTENTOS = int(os.getenv("CONSULTAR_OPERACIONES_REINTENTOS", 0))
    
    # =====================================================
    # CONFIGURACIÓN DE LOGGING
    # =====================================================
    # Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = "INFO"
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
        "version": Config.API_VERSION,
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
        "R4_UUID": Config.R4_UUID,
        "timeout": Config.REQUEST_TIMEOUT,
        "allowed_ips": Config.BANCO_IPS_PERMITIDAS,
        "reintentos": Config.R4_REINTENTOS
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
    #if Config.DEBUG:
    # Crear directorio de logs si no existe
    try:
        log_dir = os.path.dirname(Config.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"Advertencia: No se pudo crear directorio de logs: {e}")
        #Config.LOG_FILE = "r4_conecta.log"  # Fallback al directorio actual


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
    #else: pass

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
    if Config.R4_MERCHANT_ID == "":
        logger.warning("R4_MERCHANT_ID usa valor por defecto - CAMBIAR EN PRODUCCIÓN")
    
    # if Config.R4_SECRET_KEY == "clave_secreta":
    #     logger.warning("R4_SECRET_KEY usa valor por defecto - CAMBIAR EN PRODUCCIÓN")
    
    # Validar puertos
    if not (1 <= Config.API_PORT <= 65535):
        raise ValueError(f"API_PORT inválido: {Config.API_PORT}")
    
    if not (1 <= Config.DB_PORT <= 65535):
        raise ValueError(f"DB_PORT inválido: {Config.DB_PORT}")
    
    

    logger.info("Configuración validada correctamente")

# Configurar logging al importar el módulo
setup_logging()