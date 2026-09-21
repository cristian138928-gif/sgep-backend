# app/main.py
"""
Punto de entrada de la API SGEP.
Configura FastAPI, middleware, y rutas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.auth_routes import router as auth_router
from app.routes.evidencia_routes import router as evidencia_router
from app.routes.coordinador_routes import router as coordinador_router

# Cargar variables de entorno
load_dotenv()

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
    allow_origins=["*"],  # En produccion: especifico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Incluir rutas
app.include_router(auth_router)
app.include_router(evidencia_router)
app.include_router(coordinador_router)
