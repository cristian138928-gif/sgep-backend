# create_tables.py
"""
Script para crear las tablas de la base de datos.
Ejecutar una sola vez para inicializar la BD.

Uso: uv run python create_tables.py
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

# EXPLICACIÓN: Cargamos las variables de entorno para obtener la URL de la BD
load_dotenv()

# EXPLICACIÓN: Obtenemos la URL de conexión desde .env
DATABASE_URL = os.getenv("DATABASE_URL")

# EXPLICACIÓN: Importamos todos los modelos para que SQLAlchemy los conozca
# y pueda crear las tablas correspondientes
from app.models.usuario import Base, UsuarioBase, Aprendiz, Instructor, Coordinador, Evidencia, Retroalimentacion


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
