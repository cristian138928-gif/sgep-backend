# create_tables.py
"""
DEPRECADO: usar Alembic (uv run alembic upgrade head).
Script legado que creaba tablas con create_all (no migra columnas nuevas).
Se conserva solo como referencia histórica.
"""

import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

# EXPLICACIÓN: Importamos Base arriba porque ruff exige imports al inicio (E402)
from app.models.usuario import Base

# EXPLICACIÓN: Cargamos las variables de entorno para obtener la URL de la BD
load_dotenv()

# EXPLICACIÓN: Obtenemos la URL de conexión desde .env
DATABASE_URL = os.getenv("DATABASE_URL")


async def crear_tablas():
    """
    Crea todas las tablas definidas en los modelos.
    """
    # EXPLICACIÓN: Creamos el motor asincrónico de conexión
    engine = create_async_engine(DATABASE_URL, echo=True)

    # EXPLICACIÓN: Creamos todas las tablas
    # async with asegura que la conexión se cierre correctamente
    async with engine.begin() as conn:
        # EXPLICACIÓN: run_sync ejecuta código síncrono en contexto asincrónico
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tablas creadas correctamente en la base de datos")


if __name__ == "__main__":
    asyncio.run(crear_tablas())
