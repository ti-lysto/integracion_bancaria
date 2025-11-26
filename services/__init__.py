"""
SERVICIOS DE NEGOCIO
====================

En este paquete se implementa la lógica de negocio de la API:

- r4_services.py: Qué hacer con cada operación (consultas, notifica, pagos)
- r4_client.py: Cliente genérico para registrar/guardar operaciones
- r4_notifica_service.py: Flujo detallado para procesar notificaciones R4
- bancos/: Servicios específicos por banco (integraciones concretas)

Idea clave:
Los controllers reciben peticiones y delegan aquí el "qué hacer".
"""