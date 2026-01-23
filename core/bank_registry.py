"""Registro central de bancos y fábrica de servicios.

Este módulo centraliza la configuración por banco (alias, HMAC template,
nombre del SP, y la clase de servicio a usar). Permite añadir bancos nuevos
sin tocar los routers.

Por ahora todos los bancos usan el adaptador `BankR4Adapter` como servicio
por defecto (es decir, R4 es solo otro banco más). Más adelante se pueden
añadir clases específicas por banco.

Creado por: Alicson Rubio
"""
from typing import Dict, Any, Callable
from services.bancos.r4_servicio import BankR4Adapter
from services.bancos.banco_r4 import BancoR4Service

# Importar las implementaciones en español (cuando existan)
from services.bancos.banco_banesco import BancoBanescoService
from services.bancos.banco_bdv import BancoBDVService
from services.bancos.banco_bvc import BancoBVCService
from services.bancos.banco_mercantil import BancoMercantilService
from services.bancos.banco_provincial import BancoProvincialService
from services.bancos.banco_bancaribe import BancoBancaribeService
from services.bancos.banco_bancoexterior import BancoExteriorService
from services.bancos.banco_caroni import BancoCaroniService
from services.bancos.banco_sofitasa import BancoSofitasaService
from services.bancos.banco_plaza import BancoPlazaService
from services.bancos.banco_bangente import BancoBangenteService
from services.bancos.banco_bfc import BancoBfcService
from services.bancos.banco_100banco import Banco100bancoService
from services.bancos.banco_delsur import BancoDelsurService
from services.bancos.banco_tesoro import BancoTesoroService
from services.bancos.banco_agricola import BancoAgricolaService
from services.bancos.banco_bancrecer import BancoBancrecerService
from services.bancos.banco_mibanco import BancoMibancoService
from services.bancos.banco_activo import BancoActivoService
from services.bancos.banco_bancamiga import BancoBancamigaService
from services.bancos.banco_banplus import BancoBanplusService
from services.bancos.banco_bicentenario import BancoBicentenarioService
from services.bancos.banco_banfanb import BancoBanfanbService
from services.bancos.banco_bnc import BancoBncService

# Configuración mínima por banco. Se puede extender con 'hmac_template',
# 'sp_name', 'external_paths', etc.
BANK_CONFIG: Dict[str, Dict[str, Any]] = {
    # R4 como banco más
    "r4": {
        "alias": "r4",
        "service_cls": BancoR4Service
        # "hmac_template": ["IdComercio", "TelefonoComercio", "TelefonoEmisor", "Monto", "Referencia"],
        #"sp_name": "sp_r4_guardar_transaccion"
    },

    # Ejemplo: Banesco (0134) mapeado al mismo adaptador por defecto
    "0134": {
        "alias": "banesco",
        "service_cls": BancoBanescoService
        # "hmac_template": ["IdComercio", "TelefonoComercio", "TelefonoEmisor", "Monto", "Referencia"],
        # "sp_name": "sp_banesco_guardar_transaccion"
    },

    # Lista inicial de bancos solicitados. Se puede ampliar dinámicamente.
    "0102": {"alias": "bdv", "service_cls": BancoBDVService},
    "0104": {"alias": "bvc", "service_cls": BancoBVCService},
    "0105": {"alias": "mercantil", "service_cls": BancoMercantilService},
    "0108": {"alias": "provincial", "service_cls": BancoProvincialService},
    "0114": {"alias": "bancaribe", "service_cls": BancoBancaribeService},
    "0115": {"alias": "bancoexterior", "service_cls": BancoExteriorService},
    "0128": {"alias": "caroni", "service_cls": BancoCaroniService},
    "0137": {"alias": "sofitasa", "service_cls": BancoSofitasaService},
    "0138": {"alias": "plaza", "service_cls": BancoPlazaService},
    "0146": {"alias": "bangente", "service_cls": BancoBangenteService},
    "0151": {"alias": "bfc", "service_cls": BancoBfcService},
    "0156": {"alias": "100banco", "service_cls": Banco100bancoService},
    "0157": {"alias": "delsur", "service_cls": BancoDelsurService},
    "0163": {"alias": "tesoro", "service_cls": BancoTesoroService},
    "0166": {"alias": "agricola", "service_cls": BancoAgricolaService},
    "0168": {"alias": "bancrecer", "service_cls": BancoBancrecerService},
    "0169": {"alias": "mibanco", "service_cls": BancoMibancoService},
    "0171": {"alias": "activo", "service_cls": BancoActivoService},
    "0172": {"alias": "bancamiga", "service_cls": BancoBancamigaService},
    "0174": {"alias": "banplus", "service_cls": BancoBanplusService},
    "0175": {"alias": "bicentenario", "service_cls": BancoBicentenarioService},
    "0177": {"alias": "banfanb", "service_cls": BancoBanfanbService},
    "0191": {"alias": "bnc", "service_cls": BancoBncService},
}


# Índice de alias para búsquedas rápidas por nombre/alias
ALIAS_INDEX: Dict[str, Dict[str, Any]] = {}
for _code, _cfg in list(BANK_CONFIG.items()):
    alias = _cfg.get("alias")
    if alias:
        ALIAS_INDEX[alias.lower()] = {**_cfg, "code": _code}




def get_bank_config(key: str) -> Dict[str, Any]:
    """Retorna la configuración del banco por alias o código.

    Acepta tanto claves numéricas como alias (ej: '0134' o 'banesco').
    """
    if not key:
        raise KeyError("Bank key required")

    k = key.strip().lower()

    # Preferir búsqueda por alias si existe índice
    if k in ALIAS_INDEX:
        return ALIAS_INDEX[k]

    # Búsqueda directa por clave (puede ser código o alias ya existente)
    if k in BANK_CONFIG:
        return BANK_CONFIG[k]

    # Buscar por alias en la configuración (compatibilidad)
    for code, cfg in BANK_CONFIG.items():
        if cfg.get("alias") and cfg.get("alias").lower() == k:
            return {**cfg, "code": code}

    raise KeyError(f"Bank not found: {key}")


def get_service_for_bank(key: str):
    """Devuelve una instancia del servicio configurado para el banco.

    Si no existe configuración explícita para el banco, intenta usar el
    adaptador por defecto (BankR4Adapter).
    """
    cfg = None
    try:
        cfg = get_bank_config(key)
    except KeyError:
        # fallback: intentar padding si es número
        if key.isdigit():
            padded = key.zfill(4)
            try:
                cfg = get_bank_config(padded)
            except KeyError:
                cfg = None

    if not cfg:
        # Por defecto usar R4 adapter
        return BankR4Adapter(bank_code=key)

    svc_cls = cfg.get("service_cls", BankR4Adapter)
    return svc_cls(bank_code=key)


def register_bank(code: str, alias: str = None, service_cls: Callable = None, **kwargs):
    """Registrar dinámicamente un banco nuevo en el registry.

    Ejemplo:
        register_bank("9999", alias="mibanco", service_cls=MiBancoService, hmac_template=[...])
    """
    BANK_CONFIG[code] = {"alias": alias or code, "service_cls": service_cls or BankR4Adapter}
    BANK_CONFIG[code].update(kwargs)


# --- Wrappers en español (no rompen la API existente) -----------------------
def obtener_config_banco(clave: str) -> Dict[str, Any]:
    """Wrapper en español para `get_bank_config`.

    Acepta código o alias y retorna la configuración.
    """
    return get_bank_config(clave)


def obtener_servicio_para_banco(clave: str):
    """Wrapper en español para `get_service_for_bank`.

    Devuelve una instancia del servicio configurado para el banco.
    """
    return get_service_for_bank(clave)


def registrar_banco(codigo: str, alias: str = None, servicio_cls: Callable = None, **kwargs):
    """Wrapper en español para `register_bank`.

    Ejemplo:
        registrar_banco("9999", alias="mibanco", servicio_cls=MiServicioBanco)
    """
    return register_bank(codigo, alias=alias, service_cls=servicio_cls, **kwargs)

