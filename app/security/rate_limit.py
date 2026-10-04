# app/security/rate_limit.py
"""
Rate limiting en memoria (ventana deslizante) para endpoints públicos.

EXPLICACIÓN: Sin dependencias externas y testeable con reloj inyectable;
suficiente para una instancia uvicorn (estado por proceso).
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import settings


class SlidingWindowLimiter:
    """Ventana deslizante por clave: limita intentos en un rango de tiempo."""

    def __init__(self, window_seconds: float = 60.0, clock=time.monotonic) -> None:
        """
        Args:
            window_seconds: Tamaño de la ventana por defecto.
            clock: Reloj inyectable (los tests usan uno falso = sin sleeps).
        """
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        # EXPLICACIÓN: Lock porque los endpoints sync corren en threadpool
        self._lock = Lock()

    def hit(
        self, key: str, limit: int, window_seconds: float | None = None
    ) -> tuple[bool, int]:
        """
        Registra un intento para `key`.

        Returns:
            tuple: (permitido, retry_after_segundos)
        """
        ventana = window_seconds if window_seconds is not None else self._window
        ahora = self._clock()

        with self._lock:
            cola = self._hits[key]
            # EXPLICACIÓN: Purgamos intentos fuera de la ventana (deslizante)
            while cola and ahora - cola[0] >= ventana:
                cola.popleft()

            if len(cola) >= limit:
                espera = int(ventana - (ahora - cola[0])) + 1
                return False, max(espera, 1)

            cola.append(ahora)
            return True, 0

    def reset(self) -> None:
        """Vacía todos los contadores (uso en tests)."""
        with self._lock:
            self._hits.clear()


# EXPLICACIÓN: Singleton por proceso; clave = ruta + IP del cliente
limiter = SlidingWindowLimiter()


def rate_limit_auth(request: Request) -> None:
    """
    Dependencia FastAPI: lanza 429 si la IP supera el límite de la ventana.

    Aplicar con Depends(rate_limit_auth) en endpoints públicos
    (login, registro, refresh) para frenar fuerza bruta.
    """
    if not settings.rate_limit_enabled:
        return

    ip = request.client.host if request.client else "unknown"
    clave = f"{request.url.path}|{ip}"
    permitido, retry_after = limiter.hit(
        clave, settings.rate_limit_max, settings.rate_limit_window_seconds
    )

    if not permitido:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intenta de nuevo más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
