# tests/conftest.py
"""
Configuración de pytest para tests de SGEP.
Configura BD de prueba async con SQLite.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.models.usuario import Base
from app.database.connection import get_db

# EXPLICACIÓN: SQLite async para tests (no depende de PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Engine async de prueba
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Session factory para tests
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop compartido para todos los tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """
    Crea las tablas antes de cada test y las elimina después.
    autouse=True significa que se ejecuta automáticamente.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override de get_db para usar la BD de prueba."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# EXPLICACIÓN: Sobrescribimos la dependencia de BD en la app de test
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP asíncrono para tests de endpoints.
    
    Uso:
        async def test_mi_endpoint(client):
            response = await client.get("/api/v1/...")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Sesión de BD para tests de servicios.
    
    Uso:
        async def test_mi_servicio(db_session):
            resultado = await AuthService.registrar_aprendiz(db_session, ...)
    """
    async with TestSessionLocal() as session:
        yield session
