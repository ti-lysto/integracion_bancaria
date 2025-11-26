"""
WRAPPER PARA AZURE APP SERVICE
==============================
Este archivo expone la aplicación ASGI para Azure App Service
usando gunicorn con workers de uvicorn (ASGI).

Nota: No se utiliza WSGIMiddleware aquí. FastAPI es ASGI y
gunicorn con `uvicorn.workers.UvicornWorker` espera un callable ASGI.
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(__file__))

try:
    from main import app as fastapi_app
    
    # Azure (App Service Linux) cargará este callable ASGI
    # vía gunicorn -k uvicorn.workers.UvicornWorker
    application = fastapi_app
    print("FastAPI aplicación ASGI cargada correctamente para Azure")
    
except ImportError as e:
    print(f"Error de importación: {e}")
    # Debug: mostrar path actual
    print(f"Path actual: {sys.path}")
    print(f"Directorio actual: {os.listdir('.')}")
    
    # Fallback simple
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def health():
        return {"status": "fallback", "message": "Revisar imports en main.py, la aplicación no se pudo cargar."}
    
    # Exponer fallback como ASGI
    application = app

# try:
#     # Si tus imports fallan, prueba esto:
#     from main import app as fastapi_app
#     from fastapi.middleware.wsgi import WSGIMiddleware
    
#     application = WSGIMiddleware(fastapi_app)
#     print("FastAPI aplicación cargada correctamente para Azure")
    
# except ImportError as e:
#     print(f"Error de importación: {e}")
#     # Debug: mostrar path actual
#     print(f"Path actual: {sys.path}")
#     print(f"Directorio: {os.listdir('.')}")
    
#     # Fallback simple
#     from fastapi import FastAPI
#     from fastapi.middleware.wsgi import WSGIMiddleware
    
#     app = FastAPI()
    
#     @app.get("/")
#     async def health():
#         return {"status": "fallback", "message": "Revisar imports en main.py"}
    
#     application = WSGIMiddleware(app)