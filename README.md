# API R4 Conecta v3.0

> Integración bancaria (R4 Conecta) implementada con FastAPI. Documentación clara, lista para despliegue.

Este repositorio contiene únicamente el contenido de la carpeta `app/` (resto del material se mantiene local y fuera del control de versiones). Aquí encontrarás la aplicación lista para correr, los servicios y la lógica de negocio principal.

## Tabla de Contenidos

- [Resumen](#resumen)
- [Características](#características)
- [Endpoints](#endpoints)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Seguridad (HMAC)](#seguridad-hmac)
- [Estructura](#estructura)
- [Ejemplos](#ejemplos)
- [Códigos de Respuesta](#códigos-de-respuesta)
- [Problemas Comunes](#problemas-comunes)
- [Despliegue](#despliegue)
- [Roadmap](#roadmap)
- [Soporte](#soporte)

## Resumen

API REST en Python/FastAPI para integrarse con el protocolo bancario R4 Conecta v3.0 (pagos móviles, débito/crédito inmediato, domiciliaciones, C2P, consultas de tasa). Incluye autenticación HMAC, validación Pydantic, lógica de negocio central y soporte para múltiples bancos mediante adaptadores.

## Características

- Autenticación HMAC-SHA256 por endpoint
- Validación Pydantic de requests/responses
- Procedimientos almacenados (SP) para transacciones críticas
- Pool de conexiones (aiomysql) (en proceso de estabilización)
- Multi-banco vía `routers/bancos.py` y adaptador `BankR4Adapter`
- Logging estructurado (pendiente mejora request_id / JSON)
- Endpoints completos R4 + variantes multi-banco
- Código organizado para extender seguridad (rate limiting, IP whitelist, headers duros)

## Endpoints

### Consultas y Notificaciones
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /MBbcv` | Consulta tasa BCV | Obtiene el valor oficial del dólar según el BCV |
| `POST /R4consulta` | Consulta de cliente | Verifica si un cliente puede recibir pagos |
| `POST /R4notifica` | Notificación de pago | Recibe avisos de pagos móviles que nos llegan |

### Gestión de Pagos
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /R4pagos` | Dispersión de pagos | Envía dinero a múltiples personas de una vez |
| `POST /MBvuelto` | Procesamiento de vuelto | Devuelve dinero a un cliente |

### Débito y Crédito Inmediato
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /GenerarOtp` | Generar código OTP | Solicita código temporal para autorizar operaciones |
| `POST /DebitoInmediato` | Débito inmediato | Cobra dinero directamente de la cuenta del cliente |
| `POST /CreditoInmediato` | Crédito inmediato | Envía dinero directamente a la cuenta del cliente |
| `POST /CICuentas` | Crédito con cuenta | Envía dinero usando número de cuenta completo |

### Domiciliación (Cobros Automáticos)
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /TransferenciaOnline/DomiciliacionCNTA` | Domiciliación por cuenta | Configura cobros automáticos usando número de cuenta |
| `POST /TransferenciaOnline/DomiciliacionCELE` | Domiciliación por teléfono | Configura cobros automáticos usando teléfono |

### Operaciones C2P (Cliente a Persona)
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /MBc2p` | Cobro C2P | Cobra directamente al cliente en punto de venta |
| `POST /MBanulacionC2P` | Anulación C2P | Cancela un cobro C2P previamente realizado |

### Consultas de Estado
| Endpoint | Descripción | ¿Qué hace? |
|----------|-------------|------------|
| `POST /ConsultarOperaciones` | Consultar operaciones | Verifica el estado de operaciones pendientes |

## Instalación

### Paso 1: Preparar el Entorno

```bash


# Crear entorno virtual de Python
python -m venv venv

# Activar el entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Base de Datos

```sql
-- Crear base de datos
-- Ejecutar el archivo Script_Api_R4Conecta.sql
DELIMITER ;
```

### Paso 3: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar el archivo .env con tus datos
nano .env
```

## Configuración

### Archivo .env (Variables de Entorno)

```env
R4_MERCHANT_ID="id proporcionado por el banco"
DEBUG = True

# =====================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================

# Host de la base de datos (donde está instalado MySQL)
DB_HOST = "localhost"

# Puerto de MySQL (por defecto 3306)
DB_PORT = 3306

# Nombre de la base de datos
DB_NAME = "LystoLocal" 

# Usuario de MySQL
DB_USER = "root"

# Contraseña de MySQL
DB_PASSWORD = "root"
BANCO_IPS_PERMITIDAS = [
        "45.175.213.98",
        "200.74.203.91", 
        "204.199.249.3"
    ]
```


## Uso

### Iniciar el Servidor

```bash
# Si estás parado en la carpeta raiz del repo (que contiene la carpeta app/):
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 application:application #Azure
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.application:application #Azure

# Si estás dentro de la carpeta app/ (como /R4Conecta/app):
uvicorn main:app --reload --host 0.0.0.0 --port 8000
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 application:application #Azure
# Producción (lanzando desde la raíz del repo)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
# Producción (lanzando dentro de app/)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Acceder a la Documentación

Una vez iniciado el servidor, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Verificar que Funciona

```bash
# Endpoint de salud
curl http://localhost:8000/health

# Respuesta esperada:
# {"status": "ok"}
```

## Seguridad (HMAC)

### ¿Qué es HMAC y por qué es importante?

**HMAC** (Hash-based Message Authentication Code) es como una "firma digital" que garantiza:

1. **Autenticidad**: El mensaje realmente viene del banco
2. **Integridad**: Los datos no fueron modificados en el camino
3. **No repudio**: El banco no puede negar que envió el mensaje

### Cómo Funciona HMAC

```
1. El banco toma ciertos datos del mensaje
2. Los combina con una clave secreta compartida
3. Calcula un código HMAC-SHA256
4. Nos envía: mensaje + código HMAC
5. Nosotros hacemos el mismo cálculo
6. Si nuestro código coincide = mensaje auténtico
```

### Fórmulas HMAC por Endpoint

#### Consulta BCV
```
Datos: fechavalor + moneda
Ejemplo: "2024-01-15USD"
HMAC: SHA256("2024-01-15USD", clave_secreta)
```

#### Gestión de Pagos
```
Datos: monto + fecha
Ejemplo: "1000.0001/15/2024"
HMAC: SHA256("1000.0001/15/2024", clave_secreta)
```

#### Vuelto
```
Datos: TelefonoDestino + Monto + Banco + Cedula
Ejemplo: "0414123456750.000102V12345678"
HMAC: SHA256("0414123456750.000102V12345678", clave_secreta)
```

#### Débito Inmediato
```
Datos: Banco + Cedula + Telefono + Monto + OTP
Ejemplo: "0191V123456780414123456750.00123456"
HMAC: SHA256("0191V123456780414123456750.00123456", clave_secreta)
```

### Headers Requeridos

Todos los endpoints requieren estos headers:

```http
Content-Type: application/json
Authorization: [CÓDIGO_HMAC_CALCULADO]
Commerce: [TU_COMMERCE_ID]
```

## Estructura

```
├── app
│   ├── controllers
│   │   ├── endpoints_r4.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── endpoints.cpython-310.pyc
│   │       └── __init__.cpython-310.pyc
│   ├── core
│   │   ├── auth.py
│   │   ├── bank_registry.py
│   │   ├── config.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── auth.cpython-310.pyc
│   │   │   ├── bank_registry.cpython-310.pyc
│   │   │   ├── config.cpython-310.pyc
│   │   │   ├── __init__.cpython-310.pyc
│   │   │   └── security.cpython-310.pyc
│   │   └── security.py
│   ├── db
│   │   ├── connector.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── connector.cpython-310.pyc
│   │   │   ├── __init__.cpython-310.pyc
│   │   │   └── repository.cpython-310.pyc
│   │   └── repository.py
│   ├── __init__.py
│   ├── logs
│   │   └── r4_conecta.log
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-310.pyc
│   │   │   └── schemas.cpython-310.pyc
│   │   └── schemas.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   └── main.cpython-310.pyc
│   ├── README.md
│   ├── requirements.txt
│   ├── routers
│   │   ├── bancos.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── bancos.cpython-310.pyc
│   │       └── __init__.cpython-310.pyc
│   └── services
│       ├── bancos
│       │   ├── banco_100banco.py
│       │   ├── banco_activo.py
│       │   ├── banco_agricola.py
│       │   ├── banco_bancamiga.py
│       │   ├── banco_bancaribe.py
│       │   ├── banco_bancoexterior.py
│       │   ├── banco_bancrecer.py
│       │   ├── banco_banesco.py
│       │   ├── banco_banfanb.py
│       │   ├── banco_bangente.py
│       │   ├── banco_banplus.py
│       │   ├── banco_bdv.py
│       │   ├── banco_bfc.py
│       │   ├── banco_bicentenario.py
│       │   ├── banco_bnc.py
│       │   ├── banco_bvc.py
│       │   ├── banco_caroni.py
│       │   ├── banco_delsur.py
│       │   ├── banco_mercantil.py
│       │   ├── banco_mibanco.py
│       │   ├── banco_plaza.py
│       │   ├── banco_provincial.py
│       │   ├── banco_r4.py
│       │   ├── banco_sofitasa.py
│       │   ├── banco_tesoro.py
│       │   ├── base_service.py
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   ├── r4_service.py
│       │   ├── r4_servicio.py
│       │   └── template_service.py
│       ├── __init__.py
│       ├── __pycache__
│       │   ├── __init__.cpython-310.pyc
│       │   ├── r4_client.cpython-310.pyc
│       │   └── r4_services.cpython-310.pyc
│       ├── r4_client.py
│       ├── r4_notifica_service.py
│       └── r4_services.py
├── ejemplo_implementacion_banco.py
├── R4 CONECTA V3.0.pdf
├── Script_Api_R4Conecta.sql
└── test_multi_banco.py
```

### Explicación de Cada Archivo

#### `app/main.py`
- **¿Qué es?**: El archivo principal que inicia la aplicación
- **¿Qué hace?**: Configura FastAPI y registra todos los endpoints
- **¿Cuándo se modifica?**: Raramente, solo para configuración global

#### `app/controllers/endpoints_r4.py`
- **¿Qué es?**: Define todas las URLs y endpoints de la API
- **¿Qué hace?**: Recibe peticiones HTTP, valida datos, llama servicios
- **¿Cuándo se modifica?**: Al agregar nuevos endpoints o cambiar URLs

#### `app/models/schemas.py`
- **¿Qué es?**: Define la estructura de todos los datos
- **¿Qué hace?**: Valida que los datos tengan el formato correcto
- **¿Cuándo se modifica?**: Al cambiar formatos de entrada o salida

#### `app/core/auth.py`
- **¿Qué es?**: Sistema de seguridad y autenticación
- **¿Qué hace?**: Verifica que las peticiones sean auténticas
- **¿Cuándo se modifica?**: Al cambiar fórmulas HMAC o agregar seguridad

#### `app/services/r4_services.py`
- **¿Qué es?**: La "inteligencia" de la aplicación
- **¿Qué hace?**: Contiene toda la lógica de negocio
- **¿Cuándo se modifica?**: Al cambiar reglas de negocio o procesos

#### `app/db/repository.py`
- **¿Qué es?**: Interfaz con la base de datos
- **¿Qué hace?**: Guarda y consulta información en la base de datos
- **¿Cuándo se modifica?**: Al cambiar estructura de base de datos

## Ejemplos

### Ejemplo 1: Consultar Tasa BCV

```python
import requests
import hmac
import hashlib

# Configuración
base_url = "http://localhost:8000"
commerce_secret = "tu_clave_secreta"
commerce_id = "tu_commerce_id"

# Datos a enviar
payload = {
    "Moneda": "USD",
    "Fechavalor": "2024-01-15"
}

# Calcular HMAC
message = f"{payload['Fechavalor']}{payload['Moneda']}"  # "2024-01-15USD"
auth_token = hmac.new(
    commerce_secret.encode(), 
    message.encode(), 
    hashlib.sha256
).hexdigest()

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": auth_token,
    "Commerce": commerce_id
}

# Hacer petición
response = requests.post(f"{base_url}/MBbcv", json=payload, headers=headers)

# Ver respuesta
print(response.json())
# Salida esperada:
# {
#     "code": "00",
#     "fechavalor": "2024-01-15",
#     "tipocambio": 36.5314
# }
```

### Ejemplo 2: Procesar Dispersión de Pagos

```python
import requests
import hmac
import hashlib

# Configuración
base_url = "http://localhost:8000"
commerce_secret = "tu_clave_secreta"
commerce_id = "tu_commerce_id"

# Datos de dispersión
payload = {
    "monto": "1000.00",
    "fecha": "01/15/2024",
    "Referencia": "REF123456",
    "personas": [
        {
            "nombres": "Juan Pérez",
            "documento": "V12345678",
            "destino": "01020000000000000001",
            "montoPart": "600.00"
        },
        {
            "nombres": "María García",
            "documento": "V87654321",
            "destino": "01340000000000000002",
            "montoPart": "400.00"
        }
    ]
}

# Calcular HMAC: monto + fecha
message = f"{payload['monto']}{payload['fecha']}"  # "1000.0001/15/2024"
auth_token = hmac.new(
    commerce_secret.encode(), 
    message.encode(), 
    hashlib.sha256
).hexdigest()

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": auth_token,
    "Commerce": commerce_id
}

# Hacer petición
response = requests.post(f"{base_url}/R4pagos", json=payload, headers=headers)

# Ver respuesta
print(response.json())
# Salida esperada:
# {
#     "success": true,
#     "message": "Dispersión exitosa"
# }
```

### Ejemplo 3: Generar OTP y Hacer Débito

```python
# Paso 1: Generar OTP
payload_otp = {
    "Banco": "0192",
    "Monto": "50.00",
    "Telefono": "04141234567",
    "Cedula": "V12345678"
}

# HMAC para OTP: Banco + Monto + Telefono + Cedula
message_otp = f"{payload_otp['Banco']}{payload_otp['Monto']}{payload_otp['Telefono']}{payload_otp['Cedula']}"
auth_token_otp = hmac.new(commerce_secret.encode(), message_otp.encode(), hashlib.sha256).hexdigest()

headers_otp = {
    "Content-Type": "application/json",
    "Authorization": auth_token_otp,
    "Commerce": commerce_id
}

# Solicitar OTP
response_otp = requests.post(f"{base_url}/GenerarOtp", json=payload_otp, headers=headers_otp)
print("OTP solicitado:", response_otp.json())

# Paso 2: El cliente recibe SMS con código OTP (ej: 123456)
# Paso 3: Hacer débito con el OTP

payload_debito = {
    "Banco": "0192",
    "Monto": "50.00",
    "Telefono": "04141234567",
    "Cedula": "V12345678",
    "Nombre": "Juan Pérez",
    "OTP": "123456",  # Código que recibió el cliente
    "Concepto": "Pago de servicio"
}

# HMAC para débito: Banco + Cedula + Telefono + Monto + OTP
message_debito = f"{payload_debito['Banco']}{payload_debito['Cedula']}{payload_debito['Telefono']}{payload_debito['Monto']}{payload_debito['OTP']}"
auth_token_debito = hmac.new(commerce_secret.encode(), message_debito.encode(), hashlib.sha256).hexdigest()

headers_debito = {
    "Content-Type": "application/json",
    "Authorization": auth_token_debito,
    "Commerce": commerce_id
}

# Procesar débito
response_debito = requests.post(f"{base_url}/DebitoInmediato", json=payload_debito, headers=headers_debito)
print("Débito procesado:", response_debito.json())
```

## Códigos de Respuesta

### Códigos de Red Interbancaria

| Código | Significado | ¿Qué hacer? |
|--------|-------------|-------------|
| `00` | APROBADO | ✅ Transacción exitosa |
| `01` | REFERIRSE AL CLIENTE | ⚠️ Contactar al cliente |
| `12` | TRANSACCION INVALIDA | ❌ Revisar datos enviados |
| `13` | MONTO INVALIDO | ❌ Verificar monto |
| `14` | NUMERO TELEFONO RECEPTOR ERRADO | ❌ Corregir teléfono |
| `05` | TIEMPO DE RESPUESTA EXCEDIDO | ⏰ Reintentar más tarde |
| `30` | ERROR DE FORMATO | ❌ Revisar formato de datos |
| `41` | SERVICIO NO ACTIVO | ⚠️ Servicio temporalmente no disponible |
| `55` | TOKEN INVALIDO | 🔐 Revisar cálculo HMAC |
| `56` | CELULAR NO COINCIDE | ❌ Verificar teléfono y cédula |
| `80` | CEDULA O PASAPORTE ERRADO | ❌ Corregir documento |

### Códigos de Operaciones

| Código | Significado | ¿Qué hacer? |
|--------|-------------|-------------|
| `ACCP` | Operación Aceptada | ✅ Transacción completada |
| `AC00` | Operación en Espera | ⏳ Consultar estado después |
| `202` | Mensaje Recibido | ✅ Solicitud procesada |

### Códigos HTTP Estándar

| Código | Significado | Causa Común |
|--------|-------------|-------------|
| `200` | OK | ✅ Todo correcto |
| `400` | Bad Request | ❌ Datos mal formateados |
| `401` | Unauthorized | 🔐 HMAC incorrecto o headers faltantes |
| `422` | Unprocessable Entity | ❌ Datos no válidos según esquema |
| `500` | Internal Server Error | 🔧 Error interno del servidor |

## Problemas Comunes

### Problema: Error 401 (Unauthorized)

**Síntomas:**
```json
{
    "detail": "Authorization HMAC inválido para MBbcv"
}
```

**Causas posibles:**
1. HMAC calculado incorrectamente
2. Clave secreta incorrecta
3. Orden de campos incorrecto
4. Headers faltantes

**Solución:**
```python
# Verificar que el cálculo HMAC sea correcto
def debug_hmac():
    # Datos de ejemplo
    fechavalor = "2024-01-15"
    moneda = "USD"
    clave_secreta = "tu_clave_secreta"
    
    # Mensaje debe ser exactamente así
    message = f"{fechavalor}{moneda}"  # "2024-01-15USD"
    
    # Calcular HMAC
    import hmac
    import hashlib
    
    hmac_calculado = hmac.new(
        clave_secreta.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Mensaje: {message}")
    print(f"HMAC: {hmac_calculado}")
    
    return hmac_calculado

# Ejecutar debug
debug_hmac()
```

### Problema: Error 422 (Validation Error)

**Síntomas:**
```json
{
    "detail": [
        {
            "loc": ["body", "Moneda"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

**Causa:** Campos obligatorios faltantes o tipos incorrectos

**Solución:**
```python
# Verificar que todos los campos obligatorios estén presentes
payload_correcto = {
    "Moneda": "USD",        # String, obligatorio
    "Fechavalor": "2024-01-15"  # String, obligatorio
}

# Verificar tipos de datos
payload_incorrecto = {
    "Moneda": 123,          # Debería ser string
    "Fechavalor": None      # No puede ser null
}
```

### Problema: Error de Conexión a Base de Datos

**Síntomas:**
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Soluciones:**
1. Verificar que MySQL esté ejecutándose
2. Comprobar credenciales en `.env`
3. Verificar permisos del usuario
4. Comprobar firewall

```bash
# Verificar estado de MySQL
sudo systemctl status mysql

# Reiniciar MySQL si es necesario
sudo systemctl restart mysql

# Probar conexión manual
mysql -h localhost -u r4user -p r4conecta
```

### Problema: Suma de Montos No Coincide

**Síntomas:**
```json
{
    "success": false,
    "message": "No se pudo completar la dispersión",
    "error": "MONTO TOTAL NO COINCIDE"
}
```

**Causa:** En dispersión de pagos, la suma de `montoPart` no iguala `monto`

**Solución:**
```python
# Verificar cálculo
monto_total = 1000.00
personas = [
    {"montoPart": "600.00"},  # 600.00
    {"montoPart": "400.00"}   # 400.00
]

suma = sum(float(p["montoPart"]) for p in personas)
print(f"Total: {monto_total}, Suma: {suma}")  # Deben ser iguales
```

## Despliegue

### Requisitos del Servidor

**Mínimos:**
- CPU: 2 cores
- RAM: 4 GB
- Disco: 20 GB SSD
- OS: Ubuntu 20.04+ / CentOS 8+

**Recomendados:**
- CPU: 4 cores
- RAM: 8 GB
- Disco: 50 GB SSD
- OS: Ubuntu 22.04 LTS

### Configuración de Seguridad

#### 1. Firewall
```bash
# Permitir solo puertos necesarios
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # API (temporal)
sudo ufw enable
```

#### 2. SSL/TLS
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com
```

#### 3. Nginx como Proxy Reverso
```nginx
# /etc/nginx/sites-available/r4conecta
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Restricción de IPs del banco
    allow 45.175.213.98;
    allow 200.74.203.91;
    allow 204.199.249.3;
    deny all;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 4. Systemd Service
```ini
# /etc/systemd/system/r4conecta.service
[Unit]
Description=R4 Conecta API
After=network.target

[Service]
Type=exec
User=r4user
Group=r4user
WorkingDirectory=/opt/r4conecta
Environment=PATH=/opt/r4conecta/venv/bin
ExecStart=/opt/r4conecta/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Monitoreo y Logs

#### 1. Configurar Logging
```python
# app/core/logging.py
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/var/log/r4conecta/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

#### 2. Rotación de Logs
```bash
# /etc/logrotate.d/r4conecta
/var/log/r4conecta/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 r4user r4user
    postrotate
        systemctl reload r4conecta
    endscript
}
```

### Backup y Recuperación

#### 1. Backup de Base de Datos
```bash
#!/bin/bash
# /opt/scripts/backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
DB_NAME="r4conecta"

# Crear backup
mysqldump -u backup_user -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/r4conecta_$DATE.sql

# Comprimir
gzip $BACKUP_DIR/r4conecta_$DATE.sql

# Limpiar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "r4conecta_*.sql.gz" -mtime +30 -delete
```

#### 2. Cron para Backups Automáticos
```bash
# Editar crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * /opt/scripts/backup_db.sh
```



## Soporte

### Para Soporte Técnico
- **Desarrollador**: Alicson Rubio
- **Email**: [alirubio@lysto.app]
- **Documentación**: Este README.md
- **Logs**: `/app/log/r4_conecta.log`



---

## Notas Finales

Esta API está completamente implementada según las especificaciones del manual R4 Conecta v3.0. Todos los endpoints están documentados, probados y listos para producción.

**Recuerda:**
- Mantener las claves secretas seguras
- Hacer backups regulares
- Monitorear los logs constantemente
- Actualizar dependencias regularmente
- Seguir las mejores prácticas de seguridad

**¡La API está lista para procesar transacciones bancarias de forma segura y confiable!** 🎉

---

*Desarrollado por Alicson Rubio - Noviembre 2025*