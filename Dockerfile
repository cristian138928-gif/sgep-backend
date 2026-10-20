# EXPLICACIÓN: multi-stage con uv => imagen final solo con deps de producción
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# EXPLICACIÓN: copiar solo manifests primero maximiza la capa de caché de Docker
COPY pyproject.toml uv.lock ./

# EXPLICACIÓN: --frozen usa el lock exacto; --no-dev excluye ruff/pytest del runtime
RUN uv sync --frozen --no-dev --no-install-project

# EXPLICACIÓN: fase final minimalista (sin gcc, sin uv, sin group dev)
FROM python:3.12-slim

WORKDIR /app

# EXPLICACIÓN: copiar solo el .venv resuelto del builder (no el código aún)
COPY --from=builder /app/.venv /app/.venv

# EXPLICACIÓN: código después de las deps => editar app/*.py no reinstala paquetes
COPY app ./app
# EXPLICACIÓN: alembic necesario en runtime (lifespan ejecuta `alembic upgrade head`)
COPY alembic ./alembic
COPY alembic.ini ./
COPY create_tables.py ./
# EXPLICACIÓN: seed de demo ejecutable con docker compose exec api python seed_demo.py
COPY seed_demo.py ./

# EXPLICACIÓN: uploads debe existir y ser escribible por el usuario no-root
RUN mkdir -p /app/uploads && chown -R nobody:nogroup /app

# EXPLICACIÓN: correr como nobody (nunca root en contenedores expuestos)
USER nobody

# EXPLICACIÓN: solo el venv de producción en el PATH (sin uv ni herramientas dev)
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# EXPLICACIÓN: --host 0.0.0.0 accesible desde fuera del contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
