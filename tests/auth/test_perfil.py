# tests/test_perfil.py
"""
Tests para PUT /api/v1/auth/me (editar nombre + cambiar contraseña).
"""

import pytest
from httpx import AsyncClient

CLAVE_VIEJA = "OldPass1234!"
CLAVE_NUEVA = "NewPass5678!"


async def _registrar_y_login(
    client: AsyncClient, correo: str, documento: str
) -> tuple[str, str]:
    """EXPLICACIÓN: helper que devuelve (access, refresh) de un aprendiz nuevo."""
    await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Perfil Test",
            "correo_institucional": correo,
            "contraseña": CLAVE_VIEJA,
            "numero_documento": documento,
            "numero_ficha": "3388939",
            "programa": "ADSO",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"correo_institucional": correo, "contraseña": CLAVE_VIEJA},
    )
    datos = login.json()
    return datos["access_token"], datos["refresh_token"]


def _auth(token: str) -> dict[str, str]:
    """EXPLICACIÓN: cabecera Authorization reutilizable en todos los tests."""
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_put_me_cambia_nombre(client: AsyncClient):
    """Test: PUT /auth/me actualiza el nombre y persiste en /me."""
    access, _ = await _registrar_y_login(client, "nombre@test.com", "500000001")

    r = await client.put(
        "/api/v1/auth/me",
        headers=_auth(access),
        json={"nombre_completo": "Nombre Nuevo Real"},
    )
    assert r.status_code == 200
    assert r.json()["nombre_completo"] == "Nombre Nuevo Real"

    perfil = await client.get("/api/v1/auth/me", headers=_auth(access))
    assert perfil.json()["nombre_completo"] == "Nombre Nuevo Real"


@pytest.mark.asyncio
async def test_put_me_cambia_contrasena_y_login_nueva(client: AsyncClient):
    """Test: cambio de contraseña habilita login con la nueva clave."""
    access, _ = await _registrar_y_login(client, "clave@test.com", "500000002")

    r = await client.put(
        "/api/v1/auth/me",
        headers=_auth(access),
        json={
            "contraseña_actual": CLAVE_VIEJA,
            "contraseña_nueva": CLAVE_NUEVA,
        },
    )
    assert r.status_code == 200

    # La vieja ya no sirve y la nueva sí
    vieja = await client.post(
        "/api/v1/auth/login",
        json={"correo_institucional": "clave@test.com", "contraseña": CLAVE_VIEJA},
    )
    assert vieja.status_code == 401

    nueva = await client.post(
        "/api/v1/auth/login",
        json={"correo_institucional": "clave@test.com", "contraseña": CLAVE_NUEVA},
    )
    assert nueva.status_code == 200


@pytest.mark.asyncio
async def test_put_me_contrasena_actual_incorrecta_401(client: AsyncClient):
    """Test: contraseña actual errónea -> 401 y nada cambia."""
    access, _ = await _registrar_y_login(client, "mala@test.com", "500000003")

    r = await client.put(
        "/api/v1/auth/me",
        headers=_auth(access),
        json={
            "contraseña_actual": "Distinta123!",
            "contraseña_nueva": CLAVE_NUEVA,
        },
    )
    assert r.status_code == 401

    # La contraseña original sigue vigente
    ok = await client.post(
        "/api/v1/auth/login",
        json={"correo_institucional": "mala@test.com", "contraseña": CLAVE_VIEJA},
    )
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_put_me_nueva_sin_actual_400(client: AsyncClient):
    """Test: contraseña_nueva sin contraseña_actual -> 400."""
    access, _ = await _registrar_y_login(client, "sinactual@test.com", "500000004")

    r = await client.put(
        "/api/v1/auth/me",
        headers=_auth(access),
        json={"contraseña_nueva": CLAVE_NUEVA},
    )
    assert r.status_code == 400
    assert "contraseña_actual" in r.json()["detail"]


@pytest.mark.asyncio
async def test_put_me_payload_vacio_422(client: AsyncClient):
    """Test: PUT sin ningún cambio -> 422 (model_validator del esquema)."""
    access, _ = await _registrar_y_login(client, "vacio@test.com", "500000005")

    r = await client.put("/api/v1/auth/me", headers=_auth(access), json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_put_me_sin_token_401(client: AsyncClient):
    """Test: PUT /auth/me sin token -> 401."""
    r = await client.put("/api/v1/auth/me", json={"nombre_completo": "Sin Token X"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_put_me_revoca_refresh_tokens(client: AsyncClient):
    """Test: cambiar contraseña purga la cadena de refresh (re-login forzoso)."""
    access, refresh = await _registrar_y_login(client, "revoca@test.com", "500000006")

    r = await client.put(
        "/api/v1/auth/me",
        headers=_auth(access),
        json={
            "contraseña_actual": CLAVE_VIEJA,
            "contraseña_nueva": CLAVE_NUEVA,
        },
    )
    assert r.status_code == 200

    # EXPLICACIÓN: el refresh emitido ANTES del cambio ya no se puede canjear
    refresco = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert refresco.status_code == 401
