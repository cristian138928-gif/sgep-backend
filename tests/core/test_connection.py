# tests/core/test_connection.py
"""Tests de app/db/session.py (inyección de sesión)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


@pytest.mark.asyncio
async def test_get_db_entrega_sesion_y_cierra_en_finally(monkeypatch):
    """Test: get_db entrega una sesión y SIEMPRE la cierra al salir."""
    from tests.conftest import TestSessionLocal

    # EXPLICACIÓN: engine de test; el de prod no existe en CI
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", TestSessionLocal)

    # EXPLICACIÓN: espiamos close() para probar el cierre sin depender del estado interno
    cierres: list[int] = []
    close_original = AsyncSession.close

    async def _close_espiada(self: AsyncSession) -> None:
        cierres.append(id(self))
        await close_original(self)

    monkeypatch.setattr(AsyncSession, "close", _close_espiada)

    generador = get_db()
    sesion = await generador.__anext__()
    assert sesion is not None

    await generador.aclose()

    assert len(cierres) == 1
