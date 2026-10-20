# tests/test_auth_service.py
"""
Tests para AuthService.
Cubre: registro, login, validaciones.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.usuario_schema import (
    LoginSchema,
    RegistroAprendizSchema,
    RegistroCoordinadorSchema,
    RegistroInstructorSchema,
)
from app.services.auth_service import AuthService

# ====================================
# TESTS DE SERVICIO (sin HTTP)
# ====================================

@pytest.mark.asyncio
async def test_registrar_aprendiz_exitoso(db_session: AsyncSession):
    """Test: Registro de aprendiz exitoso."""
    datos = RegistroAprendizSchema(
        nombre_completo="Juan Pérez García",
        correo_institucional="juan.perez@test.com",
        contraseña="MiContra123!",
        numero_documento="1023456789",
        numero_ficha="3388939",
        programa="ADSO"
    )

    resultado = await AuthService.registrar_aprendiz(db_session, datos)

    assert resultado is not None
    assert resultado.nombre_completo == "Juan Pérez García"
    assert resultado.correo_institucional == "juan.perez@test.com"
    assert resultado.numero_ficha == "3388939"
    assert resultado.rol == "aprendiz"
    # Verificar que la contraseña se hasheó (no está en texto plano)
    assert resultado.clave_hash != "MiContra123!"


@pytest.mark.asyncio
async def test_registrar_aprendiz_email_duplicado(db_session: AsyncSession):
    """Test: Error al registrar con email ya existente."""
    datos = RegistroAprendizSchema(
        nombre_completo="Juan Pérez",
        correo_institucional="duplicado@test.com",
        contraseña="MiContra123!",
        numero_documento="1111111111",
        numero_ficha="1111111",
        programa="ADSO"
    )

    # Primer registro (exitoso)
    await AuthService.registrar_aprendiz(db_session, datos)

    # Segundo registro con mismo email (debe fallar)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await AuthService.registrar_aprendiz(db_session, datos)

    assert exc_info.value.status_code == 409
    assert "correo" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_misma_ficha_permite_varios_aprendices(db_session: AsyncSession):
    """Test: REGRESIÓN — una ficha SENA agrupa ~30 aprendices (nunca UNIQUE)."""
    base = {
        "nombre_completo": "Aprendiz de Prueba",
        "contraseña": "MiContra123!",
        "numero_ficha": "3388939",
        "programa": "ADSO",
    }
    datos_1 = RegistroAprendizSchema(**base, correo_institucional="ficha1@test.com",
                                    numero_documento="2111111111")
    datos_2 = RegistroAprendizSchema(**base, correo_institucional="ficha2@test.com",
                                    numero_documento="2222222222")

    await AuthService.registrar_aprendiz(db_session, datos_1)
    # EXPLICACIÓN: sin esto, el 2do registro de la MISMA ficha reventaba (409/500)
    aprendiz_2 = await AuthService.registrar_aprendiz(db_session, datos_2)

    assert aprendiz_2.numero_ficha == "3388939"


@pytest.mark.asyncio
async def test_login_exitoso(db_session: AsyncSession):
    """Test: Login con credenciales correctas."""
    # Primero registrar
    datos_registro = RegistroAprendizSchema(
        nombre_completo="María López",
        correo_institucional="maria.lopez@test.com",
        contraseña="SecurePass123!",
        numero_documento="1098765432",
        numero_ficha="2222222",
        programa="ADSO"
    )
    await AuthService.registrar_aprendiz(db_session, datos_registro)

    # Login
    credenciales = LoginSchema(
        correo_institucional="maria.lopez@test.com",
        contraseña="SecurePass123!"
    )
    usuario = await AuthService.login(db_session, credenciales)

    assert usuario is not None
    assert usuario.correo_institucional == "maria.lopez@test.com"


@pytest.mark.asyncio
async def test_login_contrasena_incorrecta(db_session: AsyncSession):
    """Test: Login con contraseña incorrecta."""
    from fastapi import HTTPException

    datos = RegistroAprendizSchema(
        nombre_completo="Pedro García",
        correo_institucional="pedro@test.com",
        contraseña="CorrectPass123!",
        numero_documento="1055555555",
        numero_ficha="3333333",
        programa="ADSO"
    )
    await AuthService.registrar_aprendiz(db_session, datos)

    credenciales = LoginSchema(
        correo_institucional="pedro@test.com",
        contraseña="WrongPass999!"
    )

    with pytest.raises(HTTPException) as exc_info:
        await AuthService.login(db_session, credenciales)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_crear_token_acceso():
    """Test: Generación de JWT token."""
    data = {"sub": "test@test.com", "id": 1}
    token = AuthService.crear_token_acceso(data)

    assert token is not None
    assert isinstance(token, str)
    # JWT tiene 3 partes separadas por puntos
    assert len(token.split(".")) == 3


# ====================================
# TESTS DE ENDPOINTS (con HTTP)
# ====================================

@pytest.mark.asyncio
async def test_endpoint_registro(client: AsyncClient):
    """Test: POST /api/v1/auth/registro"""
    response = await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Carlos Ruiz",
            "correo_institucional": "carlos@test.com",
            "contraseña": "TestPass123!",
            "numero_documento": "1077777777",
            "numero_ficha": "4444444",
            "programa": "ADSO"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "carlos@test.com"


@pytest.mark.asyncio
async def test_endpoint_login(client: AsyncClient):
    """Test: POST /api/v1/auth/login"""
    # Primero registrar
    await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Ana Torres",
            "correo_institucional": "ana@test.com",
            "contraseña": "SecurePass123!",
            "numero_documento": "1066666666",
            "numero_ficha": "5555555",
            "programa": "ADSO"
        }
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": "ana@test.com",
            "contraseña": "SecurePass123!"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_endpoint_login_fallido(client: AsyncClient):
    """Test: POST /api/v1/auth/login con credenciales incorrectas."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": "noexiste@test.com",
            "contraseña": "FakePass123!"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_me_devuelve_perfil(client: AsyncClient):
    """Test: GET /api/v1/auth/me retorna nombre y rol del token."""
    await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Sofia Ramirez",
            "correo_institucional": "sofia.ramirez@test.com",
            "contraseña": "SecurePass123!",
            "numero_documento": "1022233344",
            "numero_ficha": "6666666",
            "programa": "ADSO"
        }
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": "sofia.ramirez@test.com",
            "contraseña": "SecurePass123!"
        }
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nombre_completo"] == "Sofia Ramirez"
    assert data["rol"] == "aprendiz"
    assert data["correo_institucional"] == "sofia.ramirez@test.com"


@pytest.mark.asyncio
async def test_endpoint_me_sin_token_401(client: AsyncClient):
    """Test: GET /api/v1/auth/me sin token retorna 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


# ====================================
# TESTS DE get_current_user (tokens hostiles)
# ====================================

def _token_firmado(payload: dict) -> str:
    """EXPLICACIÓN: Firma con la clave real para llegar a la rama de negocio testada."""
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


@pytest.mark.asyncio
async def test_me_token_basura_401(client: AsyncClient):
    """Test: JWT corrupto -> PyJWTError -> 401 (el motivo no se filtra)."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer no.es.un.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_token_sin_sub_401(client: AsyncClient):
    """Test: JWT válido pero sin claim sub -> 401 (payload no confiable)."""
    token = _token_firmado({
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": "access",
    })
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_refresh_usado_como_access_401(client: AsyncClient):
    """Test: refresh token NO autoriza la API (claims de tipo)."""
    token = _token_firmado({
        "sub": "nadie@test.com",
        "exp": datetime.now(UTC) + timedelta(days=7),
        "type": "refresh",
    })
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_usuario_inexistente_401(client: AsyncClient):
    """Test: sub firmado de un correo sin usuario en BD -> 401."""
    token = _token_firmado({
        "sub": "fantasma@test.com",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": "access",
    })
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


# ====================================
# TESTS DE REGISTRO INSTRUCTOR
# ====================================

@pytest.mark.asyncio
async def test_registrar_instructor_exitoso(db_session: AsyncSession):
    """Test: Registro de instructor exitoso."""
    datos = RegistroInstructorSchema(
        nombre_completo="María García López",
        correo_institucional="maria.garcia@test.com",
        contraseña="InstructorPass123!",
        numero_documento="1088888888",
        centro_formacion="Centro de Salud",
        especialidad="Enfermería"
    )

    resultado = await AuthService.registrar_instructor(db_session, datos)

    assert resultado is not None
    assert resultado.nombre_completo == "María García López"
    assert resultado.rol == "instructor"
    assert resultado.centro_formacion == "Centro de Salud"
    assert resultado.especialidad == "Enfermería"


@pytest.mark.asyncio
async def test_endpoint_registro_instructor(client: AsyncClient):
    """Test: POST /api/v1/auth/registro-instructor"""
    response = await client.post(
        "/api/v1/auth/registro-instructor",
        json={
            "nombre_completo": "Pedro Martínez",
            "correo_institucional": "pedro.martinez@test.com",
            "contraseña": "InstructorPass123!",
            "numero_documento": "1099999999",
            "centro_formacion": "Centro de Tecnología",
            "especialidad": "Desarrollo de Software"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "pedro.martinez@test.com"


# ====================================
# TESTS DE REGISTRO COORDINADOR
# ====================================

@pytest.mark.asyncio
async def test_registrar_coordinador_exitoso(db_session: AsyncSession):
    """Test: Registro de coordinador exitoso."""
    datos = RegistroCoordinadorSchema(
        nombre_completo="Ana López García",
        correo_institucional="ana.lopez@test.com",
        contraseña="CoordPass123!",
        numero_documento="1077777777",
        departamento="Coordinación Académica"
    )

    resultado = await AuthService.registrar_coordinador(db_session, datos)

    assert resultado is not None
    assert resultado.nombre_completo == "Ana López García"
    assert resultado.rol == "coordinador"
    assert resultado.departamento == "Coordinación Académica"


@pytest.mark.asyncio
async def test_endpoint_registro_coordinador(client: AsyncClient):
    """Test: POST /api/v1/auth/registro-coordinador"""
    response = await client.post(
        "/api/v1/auth/registro-coordinador",
        json={
            "nombre_completo": "Carlos Ruiz Martínez",
            "correo_institucional": "carlos.ruiz@test.com",
            "contraseña": "CoordPass123!",
            "numero_documento": "1066666666",
            "departamento": "Coordinación de Programa"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "carlos.ruiz@test.com"
