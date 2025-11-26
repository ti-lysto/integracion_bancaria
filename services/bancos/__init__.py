"""
PAQUETE DE SERVICIOS POR BANCO
==============================

Aquí viven todas las integraciones específicas de bancos.
Cada archivo `banco_*.py` representa cómo hablamos con un banco diferente.

Cómo interpretarlo si no programas:
- Piensa que cada banco tiene su propio "idioma" o forma de trabajo
- Estos servicios traducen ese idioma al formato estándar de nuestra API
- Todos heredan de una base común para mantener orden y consistencia

Piezas importantes:
- base_service.py: La "plantilla" que todos deben seguir (contrato)
- r4_servicio.py: Adaptador genérico que ya sabe la lógica R4 por defecto
- r4_service.py: Versiones adicionales o utilitarios relacionados a R4
- template_service.py: Guía para crear servicios nuevos rápidamente

Sugerencia:
- Cuando agregues un banco nuevo, copia la plantilla o el servicio similar
- Implementa solo lo diferente (validaciones, SP, formateo de datos)
"""
