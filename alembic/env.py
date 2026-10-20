# alembic/env.py
"""
Entorno de Alembic asíncrono.
La URL viene de app.config (misma fuente de verdad que la app).
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# EXPLICACIÓN: prepend_sys_path=. en alembic.ini permite importar app.* desde aquí
from app.config import settings
from app.models.refresh_token import RefreshToken  # noqa: F401 - registra la tabla en Base.metadata
from app.models.usuario import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# EXPLICACIÓN: target_metadata habilita `alembic revision --autogenerate`
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline (genera SQL sin conexión)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """EXPLICACIÓN: engine async porque asyncpg no tiene modo síncrono."""
    engine = create_async_engine(settings.database_url, poolclass=pool.NullPool)

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online contra la BD real."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
