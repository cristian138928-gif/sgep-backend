# app/main.py
"""
Punto de entrada de la API SGEP.
Configura FastAPI, middleware, y rutas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.auth_routes import router as auth_router

# Cargar variables de entorno
load_dotenv()

# Crear aplicación FastAPI
app = FastAPI(
    title="SGEP - Sistema de Gestión de Evidencias",
    description="API REST para gestionar evidencias de aprendices SENA",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
)

# CORS: Permitir solicitudes desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================
# RUTAS BÁSICAS (las añadiremos después)
# ====================================

@app.get("/")
def root():
    """Ruta raíz - Verifica que API está activa"""
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
        reload=True,  # Auto-reinicia al cambiar código
        log_level="info"
    )

# Incluir rutas de autenticación en la aplicación
app.include_router(auth_router)

print("✅ API FastAPI configurada")
