# tests/test_refresh.py
"""
Tests del flujo de refresh tokens (etapa D2).
Cubre: rotación, claims de tipo, tokens inválidos.
"""

import pytest
from httpx import AsyncClient

REGISTRO = {
    "nombre_completo": "Lucia Fernandez",
    "correo_institucional": "lucia.fernandez@test.com",
    "contraseña": "SecurePass123!",
    "numero_documento": "1012345678",
    "numero_ficha": "7777777",
    "programa": "ADSO",
}


async def _login(client: AsyncClient) -> dict:
    """Registra un aprendiz (si hace falta) y devuelve el JSON del login."""
    await client.post("/api/v1/auth/registro", json=REGISTRO)
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "correo_institucional": REGISTRO["correo_institucional"],
            "contraseña": REGISTRO["contraseña"],
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_login_retorna_par_tokens(client: AsyncClient):
    """Login entrega access_token + refresh_token (no solo uno)."""
    data = await _login(client)

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_registro_entrega_refresh_token(client: AsyncClient):
    """El registro también entrega el par completo de tokens."""
    response = await client.post("/api/v1/auth/registro", json=REGISTRO)

    assert response.status_code == 201
    assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_devuelve_par_funcional(client: AsyncClient):
    """El refresh token canjea un par nuevo; el access nuevo autentica."""
    tokens = await _login(client)

    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert refresh_resp.status_code == 200
    nuevos = refresh_resp.json()
    assert "access_token" in nuevos
    assert "refresh_token" in nuevos

    # EXPLICACIÓN: El access nuevo debe servir en un endpoint protegido
    avance = await client.get(
        "/api/v1/aprendiz/avance",
        headers={"Authorization": f"Bearer {nuevos['access_token']}"},
    )
    assert avance.status_code == 200


@pytest.mark.asyncio
async def test_access_token_no_canjeable(client: AsyncClient):
    """Un access token NO se puede canjear en /refresh (claims de tipo)."""
    tokens = await _login(client)

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_no_da_acceso(client: AsyncClient):
    """Un refresh token NO autoriza llamadas a la API."""
    tokens = await _login(client)

    response = await client.get(
        "/api/v1/aprendiz/avance",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_basura_rechazado(client: AsyncClient):
    """Token corrupto en /refresh → 401."""
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "token.basura.aqui"}
    )

    assert response.status_code == 401
