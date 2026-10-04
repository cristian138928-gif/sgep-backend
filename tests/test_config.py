# tests/test_config.py
"""
Tests de validación del entorno (app.config - etapa D3).
Cubre: fail-fast, reporte acumulado de errores, tipos.
"""

import pytest

from app.config import ConfigError, load_settings


def _entorno_valido(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deja un entorno mínimo válido para aislar el error de cada test."""
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("ALGORITHM", "HS256")


def test_entorno_valido_genera_settings(monkeypatch: pytest.MonkeyPatch):
    """Con entorno correcto, load_settings devuelve Settings tipado."""
    _entorno_valido(monkeypatch)

    cfg = load_settings()

    assert len(cfg.secret_key) >= 32
    assert cfg.algorithm == "HS256"
    assert cfg.access_token_expire_minutes >= 1
    assert cfg.refresh_token_expire_days >= 1


def test_secret_key_corta_rechazada(monkeypatch: pytest.MonkeyPatch):
    """SECRET_KEY < 32 caracteres → ConfigError (no arranca la app)."""
    _entorno_valido(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "corta")

    with pytest.raises(ConfigError) as exc:
        load_settings()

    assert "SECRET_KEY" in str(exc.value)


def test_reporte_acumula_todos_los_errores(monkeypatch: pytest.MonkeyPatch):
    """Un solo ConfigError lista TODOS los problemas (arreglo de una vez)."""
    _entorno_valido(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "corta")
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("ALGORITHM", "RS256")

    with pytest.raises(ConfigError) as exc:
        load_settings()

    texto = str(exc.value)
    assert "SECRET_KEY" in texto
    assert "DATABASE_URL" in texto
    assert "ALGORITHM" in texto


def test_entero_invalido_reportado(monkeypatch: pytest.MonkeyPatch):
    """Variable no numérica → error claro con el nombre de la variable."""
    _entorno_valido(monkeypatch)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "muchas")

    with pytest.raises(ConfigError) as exc:
        load_settings()

    assert "ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc.value)
