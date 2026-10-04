# tests/test_rate_limit.py
"""
Tests de rate limiting y cabeceras de seguridad (etapa D1).
Cubre: unidad del limiter, 429 por IP, desactivación, headers OWASP.
"""

import pytest
from httpx import AsyncClient

from app.config import settings
from app.security.rate_limit import SlidingWindowLimiter, limiter

LOGIN_MALO = {
    "correo_institucional": "noexiste@test.com",
    "contraseña": "WrongPass999!",
}


@pytest.fixture(autouse=True)
def limpiar_contadores():
    """EXPLICACIÓN: El limiter es singleton; hay que vaciarlo entre tests."""
    limiter.reset()
    yield
    limiter.reset()


def test_limiter_bloquea_en_el_limite():
    """Permite `limit` intentos y bloquea el siguiente en la misma ventana."""
    reloj = SlidingWindowLimiter(window_seconds=60, clock=lambda: 0.0)

    assert reloj.hit("ip1", limit=2)[0] is True
    assert reloj.hit("ip1", limit=2)[0] is True

    permitido, retry_after = reloj.hit("ip1", limit=2)
    assert permitido is False
    assert retry_after > 0


def test_limiter_ventana_deslizante():
    """Al avanzar el reloj más allá de la ventana, vuelve a permitir."""
    ahora = {"t": 0.0}
    reloj = SlidingWindowLimiter(window_seconds=10, clock=lambda: ahora["t"])

    assert reloj.hit("ip2", limit=1)[0] is True
    assert reloj.hit("ip2", limit=1)[0] is False

    ahora["t"] = 10.0  # EXPLICACIÓN: La ventana se desliza y purga el intento viejo
    assert reloj.hit("ip2", limit=1)[0] is True


@pytest.mark.asyncio
async def test_login_superar_limite_retorna_429(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Superar el límite en /login → 429 con cabecera Retry-After."""
    monkeypatch.setattr(settings, "rate_limit_max", 2)

    assert (await client.post("/api/v1/auth/login", json=LOGIN_MALO)).status_code == 401
    assert (await client.post("/api/v1/auth/login", json=LOGIN_MALO)).status_code == 401

    response = await client.post("/api/v1/auth/login", json=LOGIN_MALO)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


@pytest.mark.asyncio
async def test_rate_limit_desactivado(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Con RATE_LIMIT_ENABLED=false nunca se responde 429."""
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    monkeypatch.setattr(settings, "rate_limit_max", 1)

    for _ in range(3):
        response = await client.post("/api/v1/auth/login", json=LOGIN_MALO)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_cabeceras_seguridad(client: AsyncClient):
    """Toda respuesta lleva cabeceras OWASP (nosniff, frame, referrer)."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
