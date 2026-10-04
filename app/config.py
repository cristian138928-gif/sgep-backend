# app/config.py
"""
Configuración centralizada del SGEP (12-factor).

EXPLICACIÓN: Un único punto de lectura de .env evita secretos repartidos
por módulo y valida el entorno ANTES de arrancar (fail-fast).
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# EXPLICACIÓN: load_dotenv inyecta .env en os.environ SOLO si la variable no existe ya
load_dotenv()


class ConfigError(RuntimeError):
    """Entorno inválido: la app NO debe arrancar."""


@dataclass
class Settings:
    """
    Configuración tipada del sistema.

    Mutable a propósito: los tests ajustan campos (ej: rate_limit_max)
    sin recargar el módulo.
    """
    secret_key: str
    algorithm: str
    database_url: str
    allowed_origins: list[str]
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    rate_limit_enabled: bool
    rate_limit_max: int
    rate_limit_window_seconds: int


def _entero(nombre: str, por_defecto: str, errores: list[str], minimo: int = 1) -> int:
    """Lee una variable como entero acumulando error (reporte único al final)."""
    crudo = os.getenv(nombre, por_defecto)
    try:
        valor = int(crudo)
    except ValueError:
        errores.append(f"{nombre} debe ser un entero (recibido: {crudo!r})")
        return minimo
    if valor < minimo:
        errores.append(f"{nombre} debe ser >= {minimo} (recibido: {valor})")
        return minimo
    return valor


def _booleano(nombre: str, por_defecto: bool) -> bool:
    """Lee una variable booleana tipo 12-factor (true/false/1/0/yes/no)."""
    crudo = os.getenv(nombre, "true" if por_defecto else "false")
    return crudo.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """
    Valida TODO el entorno y devuelve Settings.

    Acumula todos los errores y lanza UN solo ConfigError:
    el desarrollador arregla el .env completo en un arranque, no uno por uno.
    """
    errores: list[str] = []

    secret_key = os.getenv("SECRET_KEY", "")
    if len(secret_key) < 32:
        errores.append("SECRET_KEY debe tener al menos 32 caracteres")

    algorithm = os.getenv("ALGORITHM", "HS256")
    if algorithm not in {"HS256", "HS384", "HS512"}:
        errores.append(f"ALGORITHM debe ser HS256/HS384/HS512 (recibido: {algorithm})")

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        errores.append("DATABASE_URL es obligatoria")

    allowed_origins = [
        origen.strip()
        for origen in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origen.strip()
    ]

    access_minutes = _entero("ACCESS_TOKEN_EXPIRE_MINUTES", "1440", errores)
    refresh_days = _entero("REFRESH_TOKEN_EXPIRE_DAYS", "7", errores)
    rate_max = _entero("RATE_LIMIT_MAX", "10", errores)
    rate_window = _entero("RATE_LIMIT_WINDOW", "60", errores)

    if errores:
        raise ConfigError("Entorno inválido:\n- " + "\n- ".join(errores))

    return Settings(
        secret_key=secret_key,
        algorithm=algorithm,
        database_url=database_url,
        allowed_origins=allowed_origins,
        access_token_expire_minutes=access_minutes,
        refresh_token_expire_days=refresh_days,
        rate_limit_enabled=_booleano("RATE_LIMIT_ENABLED", True),
        rate_limit_max=rate_max,
        rate_limit_window_seconds=rate_window,
    )


# EXPLICACIÓN: singleton importado por toda la app; falla aquí = no arranca la API
settings = load_settings()
