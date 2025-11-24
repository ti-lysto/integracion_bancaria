"""
PAQUETE PRINCIPAL DE LA APLICACIÓN
==================================

Este directorio `app/` contiene todo el código de la API R4 Conecta.
Si no programas, piensa que aquí están las "piezas" del sistema:

- controllers/: Puertas de entrada (endpoints/URLs) que atienden a los bancos
- routers/: Rutas organizadas por tema o por banco
- services/: Lógica para procesar las operaciones (qué hacer con los datos)
- models/: Moldes (esquemas) que validan la forma de los datos
- db/: Conexión a la base de datos y acceso a procedimientos almacenados
- core/: Seguridad, configuración y utilidades centrales
- main.py: El punto de arranque de la aplicación

Todos los módulos están comentados en español y con ejemplos para que
cualquiera pueda seguir el flujo sin conocimientos técnicos.
"""