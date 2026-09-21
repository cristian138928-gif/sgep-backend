# tests/test_coordinador.py
"""
Tests para endpoints del coordinador.
Cubre: estadísticas, listado evidencias, avance aprendices.
"""

import pytest
from httpx import AsyncClient


# ====================================
# HELPERS
# ====================================

async def registrar_usuario(client: AsyncClient, email: str, rol: str = "aprendiz") -> str:
    """Registra un usuario y retorna su token JWT."""
    response = await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Test User",
            "correo_institucional": email,
            "contraseña": "TestPass123!",
            "numero_documento": "10" + email[:8].replace("@", ""),
            "numero_ficha": "1111111",
            "programa": "ADSO"
        }
    )
    return response.json()["access_token"]


async def crear_coordinador(db_session):
    """Crea un coordinador directamente en BD para tests."""
    from app.models.usuario import Coordinador
    from app.services.auth_service import AuthService

    coordinador = Coordinador(
        nombre_completo="Coordinador Test",
        correo_institucional="coordinador@test.com",
        numero_documento="1099999999",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion Academica"
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db_session.add(coordinador)
    await db_session.commit()
    await db_session.refresh(coordinador)

    return AuthService.crear_token_acceso(
        data={"sub": coordinador.correo_institucional, "id": coordinador.id_usuario}
    )


async def crear_instructor(db_session):
    """Crea un instructor directamente en BD para tests."""
    from app.models.usuario import Instructor

    instructor = Instructor(
        nombre_completo="Instructor Test",
        correo_institucional="instructor@test.com",
        numero_documento="1088888888",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro de Salud",
        especialidad="Desarrollo de Software"
    )
    instructor.establecer_contrasena("InstrPass123!")
    db_session.add(instructor)
    await db_session.commit()
    return instructor


# ====================================
# TESTS
# ====================================

@pytest.mark.asyncio
async def test_estadisticas_vacias(client: AsyncClient, db_session):
    """Test: Estadísticas con BD vacía."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evidencias"] == 0
    assert data["aprobadas"] == 0
    assert data["total_aprendices"] == 0


@pytest.mark.asyncio
async def test_listar_evidencias_vacias(client: AsyncClient, db_session):
    """Test: Listar evidencias sin datos."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/evidencias",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_listar_aprendices_vacios(client: AsyncClient, db_session):
    """Test: Listar aprendices sin datos."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/aprendices",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_listar_instructores(client: AsyncClient, db_session):
    """Test: Listar instructores."""
    await crear_instructor(db_session)
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/instructores",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_coordinador_no_autorizado(client: AsyncClient):
    """Test: Acceso sin token debe fallar."""
    response = await client.get("/api/v1/coordinador/estadisticas")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_aprendiz_no_puede_acceder_coordinador(client: AsyncClient):
    """Test: Un aprendiz no puede acceder al dashboard del coordinador."""
    token = await registrar_usuario(client, "aprendiz@test.com")

    response = await client.get(
        "/api/v1/coordinador/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
