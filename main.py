
"""
APLICACIÓN PRINCIPAL DE LA API R4 CONECTA
=========================================

Este es el archivo de nuestra API. Es el primer archivo que se ejecuta
cuando iniciamos el servidor y se encarga de configurar todo lo necesario.

¿Qué hace este archivo?
- Crea la aplicación FastAPI principal
- Configura la información básica de la API 
- Registra todos los endpoints (rutas/URLs) que definimos en otros archivos
- Configura el endpoint de salud para verificar que todo funcione
- Prepara la API para recibir peticiones del banco

¿Cuándo se ejecuta?
- Al iniciar el servidor con: uvicorn app.main:app --reload (contar con el entorno virtual activado y las dependencias instaladas)
- Es lo primero que se carga cuando arranca la aplicación

Creado por: Alicson Rubio
Fecha: 11/2025
"""

# IMPORTACIONES NECESARIAS
# ========================
from fastapi import FastAPI
# FastAPI: El framework web que usamos para crear la API REST

from controllers.endpoints import router
from core.config import validate_config, setup_logging
# Importamos controladores y configuraciones
from routers.bancos import router as bancos_router
from db.connector import close_connection_pool


# CREACIÓN DE LA APLICACIÓN PRINCIPAL
# ===================================
app = FastAPI(
    # Título que aparece en la documentación automática
    title=" API R4 Conecta v1.0 - Integración Bancaria",
    
    # Descripción detallada de qué hace nuestra API
    description="""
    ## API R4 Conecta - Notificaciones de Pagos Móviles
    
    Esta API implementa los endpoints requeridos para recibir notificaciones 
    de pagos móviles según el protocolo R4 Conecta v3.0:
    
    ### Endpoints Implementados:
    - R4bcv: Consulta de tasa de cambio BCV
    - R4notifica: Recepción de notificaciones de pagos móviles
    
    ### Características de Seguridad:
    - Validación de IPs permitidas del banco (la variable DEBUG agrega localhost 127.0.0.1 para pruebas)
    - Headers de autenticación (Authorization UUID + Commerce ID)
    - Validación de CodigoRed para transacciones aprobadas
    - Abono automático al cliente final tras validaciones
    
    ### Validaciones Implementadas:
    - Verificación de referencia, banco y monto
    - Prevención de duplicados por referencia
    - Persistencia en base de datos con stored procedures
    - Logging completo para auditoría
    
    ### Respuestas Según Especificación:
    - R4bcv: `{"code": "00", "fechavalor": "YYYY-MM-DD", "tipocambio": float}`
    - R4notifica: `{"abono": true/false}`
    
    Desarrollado por: Alicson Rubio | Fecha: Noviembre 2025
    """,
    
    # Versión actual de nuestra API
    version="1.0.0",
    
    # Información de contacto (opcional)
    contact={
        "name": "Alicson Rubio",
        "email": "alirubio@lysto.app",
    },
    
    # Información de licencia (opcional)
    license_info={  
        "name": "Propietario - Lysto",
    },
)

# CONFIGURAR LOGGING Y VALIDAR CONFIGURACIÓN
# ==========================================
#print("Hola Mundo de main.py")
setup_logging()

try:
    validate_config()
except ValueError as e:
    print(f"Error de configuración: {e}")
    exit(1)
except Exception as e:
    print(f"Error inesperado en configuración: {e}")
    exit(1)

# REGISTRO DE RUTAS/ENDPOINTS
# ===========================
# Registrar todos los endpoints R4
app.include_router(router, tags=["R4 Conecta"])
# Registrar router genérico para múltiples bancos (usa el mismo modelo R4 por ahora)
app.include_router(bancos_router, tags=["Bancos"])


# ENDPOINTS REGISTRADOS VÍA ROUTER
# ================================
# Los endpoints /health, /R4consulta, /R4notifica y / están definidos
# en app.controllers.endpoints y registrados automáticamente


# INFORMACIÓN ADICIONAL SOBRE ESTE ARCHIVO
# ========================================
@app.on_event("shutdown")
async def on_shutdown():
    await close_connection_pool()

"""
PUNTOS IMPORTANTES SOBRE main.py:

1. PUNTO DE ENTRADA:
   - Este archivo es el "punto de entrada" de toda la aplicación
   - Cuando ejecutas "uvicorn app.main:app", está buscando la variable "app" en este archivo

2. CONFIGURACIÓN CENTRALIZADA:
   - Aquí se configura toda la información básica de la API
   - El título, descripción y versión aparecen en la documentación 
   - Se puede acceder a la documentación en: http://localhost:8000/docs

3. REGISTRO DE RUTAS:
   - app.include_router(endpoints.router) registra todos los endpoints
   - Sin esta línea, ningún endpoint funcionaría

4. ENDPOINT DE SALUD:
   - /health es un endpoint especial para verificar que todo funcione
   - No requiere autenticación (es público)
   - Muy útil para monitoreo y pruebas rápidas

5. ESCALABILIDAD:
   - Si en el futuro necesitamos más grupos de endpoints, los agregamos aquí
   - Ejemplo: app.include_router(admin_router, prefix="/admin")
   - Mantiene el código organizado y modular

6. CONFIGURACIÓN ADICIONAL:
   - Aquí se pueden agregar middlewares (funciones que se ejecutan en cada petición)
   - Configuración de CORS (para permitir peticiones desde navegadores)
   - Configuración de logging global
   - Manejo de errores globales

EJEMPLO DE USO:
Para iniciar la aplicación:
    iniciar el entorno virtual y ejecutar:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Para verificar que funciona:
    curl http://localhost:8000/health
    
Para ver la documentación:
    http://localhost:8000/docs
"""