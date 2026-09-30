# app/database/connection.py
"""
Gestión de conexiones asincrónicas a la BD.
SQLAlchemy Async + PostgreSQL
"""

# Importar herramientas para conexiones asincrónicas
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno (.env)
load_dotenv()

# Obtener URL de conexión desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

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
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Entrega la sesión a FastAPI
        finally:
            await session.close()  # Cierra siempre, incluso si hay error

print("Conexión a BD configurada")
