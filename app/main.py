# app/main.py
"""
Punto de entrada de la API SGEP.
Configura FastAPI, middleware, lifespan de alertas y rutas.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.routes.aprendiz_routes import router as aprendiz_router
from app.routes.asignacion_routes import router as asignacion_router
from app.routes.auth_routes import router as auth_router
from app.routes.coordinador_routes import router as coordinador_router
from app.routes.evidencia_routes import router as evidencia_router
from app.routes.instructor_routes import router as instructor_router
from app.routes.notificacion_routes import router as notificacion_router
from app.routes.retroalimentacion_routes import router as retroalimentacion_router
from app.services.notificacion_service import NotificacionService

logger = logging.getLogger("sgep.alertas")

# EXPLICACIÓN: Orígenes desde settings (app.config valida .env al importar)
ALLOWED_ORIGINS = settings.allowed_origins


async def _loop_alertas_vencimiento() -> None:
    """
    EXPLICACIÓN: Materializa alertas de vencimiento cada N minutos
    (ALERTAS_INTERVALO_MINUTOS; 0 desactiva la tarea). Nunca muere:
    un fallo de BD solo pospone la siguiente ronda.
    """
    while True:
        try:
            async with AsyncSessionLocal() as session:
                creadas = await NotificacionService.generar_alertas_vencimiento(session)
            if creadas:
                logger.info("Alertas de vencimiento creadas: %s", creadas)
        except Exception:  # noqa: BLE001 - EXPLICACIÓN: el loop debe sobrevivir a errores
            logger.exception("Fallo generando alertas de vencimiento")
        await asyncio.sleep(settings.alertas_intervalo_minutos * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranca/detiene la tarea periódica de alertas junto al servidor."""
    tarea = None
    if settings.alertas_intervalo_minutos > 0:
        tarea = asyncio.create_task(_loop_alertas_vencimiento())
    yield
    if tarea:
        tarea.cancel()


# Crear aplicacion FastAPI
app = FastAPI(
    title="SGEP - Sistema de Gestion de Evidencias",
    description="API REST para gestionar evidencias de aprendices SENA",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
    lifespan=lifespan,
)

# CORS: Permitir solicitudes desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # EXPLICACIÓN: Usamos variable de entorno para seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    """EXPLICACIÓN: Cabeceras mínimas OWASP (anti sniffing/clickjacking)."""
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    return respuesta


@app.get("/")
def root():
    """Ruta raiz - Verifica que API esta activa"""
    return {
        "mensaje": "Bienvenido a SGEP",
        "version": "0.1.0",
        "docs": "http://localhost:8000/api/docs"
    }


@app.get("/health")
def health_check():
    """Health check para DevOps/Kubernetes"""
    return {"status": "healthy", "servicio": "SGEP API"}


# Punto de entrada si ejecutas directo
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # EXPLICACIÓN: ruta importable desde la raíz del proyecto
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Incluir rutas
app.include_router(auth_router)
app.include_router(evidencia_router)
app.include_router(coordinador_router)
app.include_router(instructor_router)
app.include_router(asignacion_router)
app.include_router(retroalimentacion_router)
app.include_router(aprendiz_router)
app.include_router(notificacion_router)
