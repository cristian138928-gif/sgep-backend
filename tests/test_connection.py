# tests/test_connection.py
"""
Tests de app/database/connection.py (inyección de sesión).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db


@pytest.mark.asyncio
async def test_get_db_entrega_sesion_y_cierra_en_finally(monkeypatch):
    """Test: get_db entrega una sesión y SIEMPRE la cierra al salir (finally)."""
    from tests.conftest import TestSessionLocal

    # EXPLICACIÓN: engine de test; el de prod no existe en CI
    monkeypatch.setattr("app.database.connection.AsyncSessionLocal", TestSessionLocal)

    # EXPLICACIÓN: espiamos close() para probar el finally sin dependir del estado interno
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
