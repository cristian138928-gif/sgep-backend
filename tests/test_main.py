# tests/test_main.py
"""
Tests de app/main.py: raíz, loop de alertas y lifespan.
"""

import asyncio

import pytest
from httpx import AsyncClient

from app.config import settings
from app.main import _loop_alertas_vencimiento, app, lifespan

# ====================================
# RUTAS BÁSICAS
# ====================================

async def test_root_200(client: AsyncClient):
    """Test: GET / responde con la bienvenida y la versión."""
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["mensaje"] == "Bienvenido a SGEP"


# ====================================
# LOOP DE ALERTAS (lifespan)
# ====================================

@pytest.mark.asyncio
async def test_loop_alertas_sobrevive_y_duerme(monkeypatch):
    """Test: el loop siempre duerme entre rondas aunque la BD falle."""
    from tests.conftest import TestSessionLocal

    # EXPLICACIÓN: engine de test para no tocar la BD real del entorno
    monkeypatch.setattr("app.main.AsyncSessionLocal", TestSessionLocal)

    esperas: list[float] = []

    async def _sleep_que_cancela(segundos: float) -> None:
        esperas.append(segundos)
        # EXPLICACIÓN: CancelledError es BaseException => no la atrapa el while
        raise asyncio.CancelledError

    monkeypatch.setattr(asyncio, "sleep", _sleep_que_cancela)

    with pytest.raises(asyncio.CancelledError):
        await _loop_alertas_vencimiento()

    assert esperas == [settings.alertas_intervalo_minutos * 60]


@pytest.mark.asyncio
async def test_loop_alertas_sobrevive_a_error_de_bd(monkeypatch):
    """Test: un fallo de BD no mata el loop (except -> sigue y duerme)."""
    class _SesionRota:
        """EXPLICACIÓN: sesión falsa que revienta al entrar (simula BD caída)."""

        async def __aenter__(self):
            raise RuntimeError("BD caida")

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr("app.main.AsyncSessionLocal", _SesionRota)

    esperas: list[float] = []

    async def _sleep_que_cancela(segundos: float) -> None:
        esperas.append(segundos)
        raise asyncio.CancelledError

    monkeypatch.setattr(asyncio, "sleep", _sleep_que_cancela)

    with pytest.raises(asyncio.CancelledError):
        await _loop_alertas_vencimiento()

    # EXPLICACIÓN: llegó a dormir => el except del loop hizo su trabajo
    assert esperas == [settings.alertas_intervalo_minutos * 60]


@pytest.mark.asyncio
async def test_lifespan_crea_y_cancela_tarea(monkeypatch):
    """Test: con intervalo > 0 arranca la tarea y al salir la cancela."""
    from tests.conftest import TestSessionLocal

    # EXPLICACIÓN: las migraciones requieren BD viva => fuera del alcance de este test
    monkeypatch.setattr("app.main._aplicar_migraciones", lambda: None)
    monkeypatch.setattr(settings, "alertas_intervalo_minutos", 1)
    monkeypatch.setattr("app.main.AsyncSessionLocal", TestSessionLocal)

    async with lifespan(app):
        tareas = [
            tarea
            for tarea in asyncio.all_tasks()
            if tarea.get_coro().__qualname__ == "_loop_alertas_vencimiento"
        ]
        assert len(tareas) == 1

    # EXPLICACIÓN: tras salir, lifespan.cancel() ya se ejecutó
    await asyncio.sleep(0)


# ====================================
# MIGRACIONES EN LIFESPAN
# ====================================

def test_migraciones_loguea_upgrades(monkeypatch, caplog):
    """Test: si alembic reporta upgrades, cada línea se loguea como INFO."""
    import logging
    from unittest.mock import Mock

    from app.main import _aplicar_migraciones

    salida = (
        "INFO  [alembic.runtime.migration] Running upgrade 41f739ff838f -> head\n"
    )
    # EXPLICACIÓN: Mock evita ejecutar alembic real (requiere BD viva)
    monkeypatch.setattr(
        "app.main.subprocess.run",
        Mock(return_value=Mock(stdout=salida)),
    )

    with caplog.at_level(logging.INFO, logger="sgep.alertas"):
        _aplicar_migraciones()

    # EXPLICACIÓN: caplog.text ya viene formateado (logger usa %s args)
    assert "Running upgrade" in caplog.text


def test_migraciones_sin_cambios_no_loguea(monkeypatch, caplog):
    """Test: "sin cambios" => stdout vacío => cero logs INFO."""
    import logging
    from unittest.mock import Mock

    from app.main import _aplicar_migraciones

    monkeypatch.setattr(
        "app.main.subprocess.run",
        Mock(return_value=Mock(stdout="")),
    )

    with caplog.at_level(logging.INFO, logger="sgep.alertas"):
        _aplicar_migraciones()

    assert "Running upgrade" not in caplog.text


def test_migraciones_falla_loguea_y_propaga(monkeypatch, caplog):
    """Test: alembic falla => stderr en log ERROR y la excepción se re-lanza."""
    import logging
    import subprocess
    from unittest.mock import Mock

    from app.main import _aplicar_migraciones

    error = subprocess.CalledProcessError(
        returncode=1, cmd=["alembic"], stderr="ConnectionRefusedError"
    )
    monkeypatch.setattr("app.main.subprocess.run", Mock(side_effect=error))

    with caplog.at_level(logging.ERROR, logger="sgep.alertas"), pytest.raises(
        subprocess.CalledProcessError
    ):
        _aplicar_migraciones()

    assert "ConnectionRefusedError" in caplog.text

