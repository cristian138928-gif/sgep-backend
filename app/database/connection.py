# app/database/connection.py
"""
Gestión de conexiones asincrónicas a la BD.
SQLAlchemy Async + PostgreSQL
"""

# Importar herramientas para conexiones asincrónicas
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# EXPLICACIÓN: Una sola fuente de verdad (app.config) valida DATABASE_URL antes de usarla
DATABASE_URL = settings.database_url

# MOTOR ASINCRÓNICO:
# - echo=False: No muestra SQL en consola (cambiar a True para debugging)
# - pool_pre_ping=True: Verifica que la conexión esté activa antes de usar
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# FACTORY DE SESIONES:
# Crea una nueva sesión de BD para cada request de FastAPI
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,  # Sesión asincrónica
    expire_on_commit=False,  # No expira objetos después de commit
    autocommit=False,  # Controlar transacciones manualmente
    autoflush=False,  # Controlar flush manualmente
)

async def get_db():
    """
    INYECCIÓN DE DEPENDENCIA para FastAPI.
    - FastAPI automáticamente crea una sesión nueva por request
    - Se cierra automáticamente después de la respuesta
    - Esto es una "función generadora" (yield = pausa la ejecución)
    """
    # EXPLICACIÓN: el async with ya cierra la sesión en __aexit__ (sin try/finally redundante)
    async with AsyncSessionLocal() as session:
        yield session

print("Conexión a BD configurada")
