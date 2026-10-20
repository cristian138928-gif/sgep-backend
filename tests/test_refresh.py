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


# ====================================
# DETECCIÓN DE REUSO (rotación real)
# ====================================

@pytest.mark.asyncio
async def test_reuso_invalida_cadena_completa(client: AsyncClient, db_session):
    """Reusar un refresh YA fuera de la gracia => 401 y TODA la cadena muere."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from app.models.refresh_token import RefreshToken

    tokens = await _login(client)

    # Rota A -> B (A queda usado)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    nuevos = resp.json()

    # EXPLICACIÓN: envejecemos la rotación para salir de la gracia de 15s (ataque real)
    viejo = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.usado == 1)
        )
    ).scalars().one()
    viejo.usada_en = datetime.now(UTC) - timedelta(seconds=60)
    await db_session.commit()

    # Reusar A (el viejo) => 401 por reuso
    resp_a = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp_a.status_code == 401
    # EXPLICACIÓN: el borrado de cadena mató también al token B de la rotación
    resp_b = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": nuevos["refresh_token"]}
    )
    assert resp_b.status_code == 401


@pytest.mark.asyncio
async def test_reuso_dentro_de_gracia_es_carrera(client: AsyncClient):
    """Dos pestañas canjeando casi a la vez => 200 (carrera benigna, no robo)."""
    tokens = await _login(client)

    r1 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r1.status_code == 200

    # EXPLICACIÓN: reuso INMEDIATO (la 2da pestaña) => dentro de la gracia de 15s
    r2 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r2.status_code == 200

    # Y la cadena NO fue purgada: el token de la 1ª rotación sigue sirviendo
    r3 = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": r1.json()["refresh_token"]}
    )
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_refresh_sin_jti_rechazado(client: AsyncClient):
    """Un refresh bien firmado pero sin jti (tokens pre-feature) => 401."""
    from app.services.auth_service import AuthService

    tokens = await _login(client)
    # EXPLICACIÓN: decodificamos el refresh para reconstruir los claims sin jti
    from jwt import decode as jwt_decode

    from app.config import settings

    payload = jwt_decode(
        tokens["refresh_token"], settings.secret_key, algorithms=[settings.algorithm]
    )
    sin_jti = AuthService.crear_token_refresh(
        {k: v for k, v in payload.items() if k != "jti"}
    )

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": sin_jti}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rotacion_deja_jti_usado_y_nuevo_activo(client: AsyncClient, db_session):
    """Tras rotar: el jti viejo queda usado=1 y el nuevo usado=0."""
    from sqlalchemy import select

    from app.models.refresh_token import RefreshToken

    tokens = await _login(client)
    await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    registros = (
        (await db_session.execute(select(RefreshToken))).scalars().all()
    )
    # EXPLICACIÓN: registro + login + rotación = 3 jtis; solo el rotado queda usado
    assert len(registros) == 3
    assert sorted(r.usado for r in registros) == [0, 0, 1]
