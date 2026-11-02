# tests/test_logout.py
"""
Tests de POST /api/v1/auth/logout (revoca refresh) y purga de caducados.

EXPLICACIÓN: el access caduca solo; sin logout el refresh seguiría canjeando
7 días aunque el usuario "cerró sesión" en la SPA.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from app.models.usuario import UsuarioBase
from app.services.auth_service import AuthService
from tests.test_refresh import REGISTRO, _login

OTRO_CORREO = "otro.usuario@test.com"


async def _registrar_otro(client: AsyncClient) -> dict:
    """Segundo aprendiz distinto (para probar que el logout no es global)."""
    registro = {**REGISTRO, "correo_institucional": OTRO_CORREO, "numero_documento": "87654321"}
    await client.post("/api/v1/auth/registro", json=registro)
    respuesta = await client.post(
        "/api/v1/auth/login",
        json={"correo_institucional": OTRO_CORREO, "contraseña": REGISTRO["contraseña"]},
    )
    assert respuesta.status_code == 200
    return respuesta.json()


# ====================================
# LOGOUT (revoca el refresh presentado)
# ====================================

@pytest.mark.asyncio
async def test_logout_revoca_el_refresh(client: AsyncClient):
    """Tras logout, el refresh presentado ya no se puede canjear."""
    tokens = await _login(client)

    resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200

    canje = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert canje.status_code == 401


@pytest.mark.asyncio
async def test_logout_es_idempotente(client: AsyncClient):
    """Repetir logout (o mandar basura) responde 200: nunca rompe la SPA."""
    tokens = await _login(client)

    primera = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    segunda = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    basura = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "token.basura.aqui"}
    )

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert basura.status_code == 200


@pytest.mark.asyncio
async def test_logout_sin_refresh_da_422(client: AsyncClient):
    """Payload sin refresh_token => validación Pydantic 422."""
    respuesta = await client.post("/api/v1/auth/logout", json={})

    assert respuesta.status_code == 422


@pytest.mark.asyncio
async def test_logout_no_mata_otro_usuario(client: AsyncClient):
    """Revocar de A deja el refresh de B intacto (revocación por jti)."""
    tokens_a = await _login(client)
    tokens_b = await _registrar_otro(client)

    await client.post("/api/v1/auth/logout", json={"refresh_token": tokens_a["refresh_token"]})

    canje_a = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens_a["refresh_token"]}
    )
    canje_b = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens_b["refresh_token"]}
    )

    assert canje_a.status_code == 401
    assert canje_b.status_code == 200


@pytest.mark.asyncio
async def test_logout_con_refresh_vencido_tambien_revoca(client: AsyncClient):
    """verify_exp=False en el logout: cerrar sesión con token caducado funciona."""
    from jwt import decode as jwt_decode
    from jwt import encode as jwt_encode

    from app.config import settings

    tokens = await _login(client)
    payload = jwt_decode(
        tokens["refresh_token"], settings.secret_key, algorithms=[settings.algorithm]
    )
    # EXPLICACIÓN: re-firmamos con exp en el pasado (un refresh de hace 8 días)
    vencido = jwt_encode(
        {**payload, "exp": datetime.now(UTC) - timedelta(days=8)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    respuesta = await client.post("/api/v1/auth/logout", json={"refresh_token": vencido})

    assert respuesta.status_code == 200


# ====================================
# PURGA DE CADUCADOS (housekeeping)
# ====================================

@pytest.mark.asyncio
async def test_purga_borra_solo_los_expirados(client: AsyncClient, db_session):
    """purgar_refresh_expirados borra vencidos y conserva los vivos."""
    await _login(client)
    usuario = (
        await db_session.execute(
            select(UsuarioBase).where(
                UsuarioBase.correo_institucional == REGISTRO["correo_institucional"]
            )
        )
    ).scalars().one()

    db_session.add(
        RefreshToken(
            jti="purga-expirado",
            id_usuario=usuario.id_usuario,
            expira_en=datetime.now(UTC) - timedelta(days=1),
        )
    )
    db_session.add(
        RefreshToken(
            jti="purga-vivo",
            id_usuario=usuario.id_usuario,
            expira_en=datetime.now(UTC) + timedelta(days=5),
        )
    )
    await db_session.commit()

    borrados = await AuthService.purgar_refresh_expirados(db_session)
    restantes = {
        r.jti for r in (await db_session.execute(select(RefreshToken))).scalars().all()
    }

    assert borrados >= 1
    assert "purga-expirado" not in restantes
    assert "purga-vivo" in restantes


@pytest.mark.asyncio
async def test_purga_sin_expirados_devuelve_cero():
    """Tras una limpieza, la siguiente ronda no borra nada (0, no error)."""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        await AuthService.purgar_refresh_expirados(session)  # limpia restos
        borrados = await AuthService.purgar_refresh_expirados(session)

    assert borrados == 0
