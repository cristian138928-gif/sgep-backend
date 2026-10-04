# app/main.py
"""
Punto de entrada de la API SGEP.
Configura FastAPI, middleware, y rutas.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.aprendiz_routes import router as aprendiz_router
from app.routes.asignacion_routes import router as asignacion_router
from app.routes.auth_routes import router as auth_router
from app.routes.coordinador_routes import router as coordinador_router
from app.routes.evidencia_routes import router as evidencia_router
from app.routes.instructor_routes import router as instructor_router
from app.routes.retroalimentacion_routes import router as retroalimentacion_router

# EXPLICACIÓN: Orígenes desde settings (app.config valida .env al importar)
ALLOWED_ORIGINS = settings.allowed_origins

# Crear aplicacion FastAPI
app = FastAPI(
    title="SGEP - Sistema de Gestion de Evidencias",
    description="API REST para gestionar evidencias de aprendices SENA",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
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
