# tests/conftest.py
"""
Configuración de pytest para tests de SGEP.
Configura BD de prueba async con SQLite.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.connection import get_db
from app.main import app
from app.models.usuario import Base

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


# ====================================
# HELPERS CENTRALIZADOS
# ====================================

async def crear_coordinador_token(db_session) -> str:
    """Crea coordinador y retorna JWT."""
    from app.models.usuario import Coordinador
    from app.services.auth_service import AuthService

    coord = Coordinador(
        nombre_completo="Coordinador Test",
        correo_institucional="coordinador@test.com",
        numero_documento="1099999999",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion Academica"
    )
    coord.establecer_contrasena("CoordPass123!")
    db_session.add(coord)
    await db_session.commit()
    await db_session.refresh(coord)
    return AuthService.crear_token_acceso(
        data={"sub": coord.correo_institucional, "id": coord.id_usuario}
    )


async def crear_aprendiz(db_session, email="aprendiz1@test.com", ficha="1111111"):
    """Crea un aprendiz en BD."""
    from app.models.usuario import Aprendiz

    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Test",
        correo_institucional=email,
        numero_documento="10" + str(hash(email))[:8],
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha=ficha,
        programa="ADSO"
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def crear_instructor(db_session, email="instructor@test.com"):
    """Crea instructor en BD."""
    from app.models.usuario import Instructor

    inst = Instructor(
        nombre_completo="Instructor Test",
        correo_institucional=email,
        numero_documento="10" + str(hash(email))[:8],
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software"
    )
    inst.establecer_contrasena("InstructorPass123!")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    return inst


async def crear_evidencia(db_session, id_aprendiz, titulo="Test", estado="Pendiente"):
    """Crea una evidencia en BD."""
    from app.models.usuario import Evidencia

    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo=titulo,
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test/test.pdf",
        estado=estado
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia
