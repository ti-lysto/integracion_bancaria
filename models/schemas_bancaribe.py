

# IMPORTACIONES NECESARIAS
# ========================
from pydantic import BaseModel, Field
# BaseModel: Clase base para crear esquemas de datos
# Field: Para agregar validaciones y descripciones a los campos

from typing import Optional, Dict, Any,List
# Optional: Para campos que pueden ser nulos
# Dict: Para diccionarios (clave-valor)
# Any: Para cualquier tipo de dato


# ESQUEMAS PARA CONSULTA DE TASA BCV
# ==================================
class TasaBcv(BaseModel):
    fechavalor: str
    tipocambio: str
    valor: float

class BancaribeBcvRequest(BaseModel):
    """
    DATOS QUE RECIBIMOS PARA CONSULTAR LA TASA DEL BCV
    
    ¿Qué es el BCV?
    - Banco Central de Venezuela
    - Entidad que establece la tasa de cambio oficial del dólar
    
    ¿Para qué sirve esta consulta?
    - Para saber cuántos bolívares vale un dólar oficialmente
    - Para hacer conversiones de moneda precisas
    - Para cumplir con regulaciones cambiarias
    
    Campos requeridos:
    - Moneda: Código ISO de la moneda (ej: "USD", "EUR")
    - Fechavalor: Fecha para la cual queremos la tasa (formato: YYYY-MM-DD)
    """
    
    Moneda: str  
    FechaInicio: str  
    FechaFin: str  

class RBancaribeBcvResponse(BaseModel):
    """
    RESPUESTA QUE ENVIAMOS CON LA TASA DEL BCV
    
    ¿Qué devolvemos?
    - El código de resultado de la operación
    - La fecha consultada (confirmación)
    - El valor de la tasa de cambio
    
    Ejemplo de respuesta:
    {
        "code": "00",
        "fechavalor": "2024-01-15", 
        "tipocambio": 36.5314
    }
    
    Esto significa: El 15 de enero de 2024, 1 USD = 36.5314 VES
    """
    listatasa: List  # Lista de tasas (puede ser vacía)
    # fechavalor: str  # Fecha consultada
    # tipocambio: float  # Valor de la tasa de cambio


# ESQUEMAS PARA CONSULTA DE OPERACONES
# =================================
class BancaribeConsultaRequest(BaseModel):
        
    IdCliente: str  # Cédula del cliente (obligatorio)
    Monto: Optional[str]  # Monto a recibir (opcional)
    TelefonoComercio: Optional[str]  # Nuestro teléfono (opcional)

class BancaribeConsultaResponse(BaseModel):
    """
    RESPUESTA A LA CONSULTA DE CLIENTE
    
    ¿Qué respondemos?
    - true: Sí conocemos al cliente y puede recibir el pago
    - false: No lo conocemos o no puede recibir el pago
    
    Esta respuesta determina si el banco procede con el pago o lo rechaza.
    """
    
    status: bool  # true = acepta, false = rechaza


# ESQUEMAS PARA NOTIFICACIÓN DE PAGO
# ==================================
class BancaribenotificationsRequest(BaseModel):
    
    amount: str 
    bankName: str 
    clientPhone: str 
    commercePhone: str 
    creditorAccount: str 
    currencyCode: str 
    date: str 
    debtorAccount: str 
    debtorID: str 
    destinyBankReference: str
    originBankCode: str 
    originBankReference: str
    paymentType: str 
    time: str 

class BancaribenotificationsResponse(BaseModel):
        
    message : str = "Success"# "Success" o mensaje de error
    statusCode: int = 200 # 200 para éxito, otro código para error


