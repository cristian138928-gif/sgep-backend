# tests/test_aprendiz.py
"""
Tests para endpoints de aprendiz.
Cubre: avance, seguridad RBAC.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.usuario_schema import RegistroAprendizSchema
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_mi_avance_vacio(client: AsyncClient, db_session: AsyncSession):
    """Test: Avance sin evidencias retorna 0%."""
    # Registrar aprendiz
    datos = RegistroAprendizSchema(
        nombre_completo="Juan Pérez García",
        correo_institucional="juan.perez@test.com",
        contraseña="MiContra123!",
        numero_documento="1023456789",
        numero_ficha="3388939",
        programa="ADSO"
    )
    await AuthService.registrar_aprendiz(db_session, datos)

    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": "juan.perez@test.com",
            "contraseña": "MiContra123!"
        }
    )
    token = login_resp.json()["access_token"]

    # Consultar avance
    response = await client.get(
        "/api/v1/aprendiz/avance",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evidencias"] == 0
    assert data["aprobadas"] == 0
    assert data["porcentaje_avance"] == 0.0


@pytest.mark.asyncio
async def test_avance_instructor_no_autorizado(client: AsyncClient, db_session: AsyncSession):
    """Test: Instructor no puede acceder a avance de aprendiz."""
    from app.schemas.usuario_schema import RegistroInstructorSchema

    datos = RegistroInstructorSchema(
        nombre_completo="María García López",
        correo_institucional="maria.garcia@test.com",
        contraseña="InstructorPass123!",
        numero_documento="1088888888",
        centro_formacion="Centro de Salud",
        especialidad="Enfermería"
    )
    await AuthService.registrar_instructor(db_session, datos)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": "maria.garcia@test.com",
            "contraseña": "InstructorPass123!"
        }
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/aprendiz/avance",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "aprendices" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_avance_sin_auth(client: AsyncClient):
    """Test: Sin token retorna 401 (RFC 6750: no autenticado, distinto de 403)."""
    response = await client.get("/api/v1/aprendiz/avance")
    assert response.status_code == 401
