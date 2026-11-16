# docs/DESPLIEGUE_CIERRE.md
# Despliegue y Cierre - SGEP

Guía operativa para dejar el sistema en ejecución estable (demo/servidor) y cerrar la entrega.

## 1. Requisitos de despliegue
- Docker Engine + Docker Compose v2 (recomendado) o servidor con Python 3.12+, Node 20+, PostgreSQL 16.
- Puerto libre: `3000` (SPA/nginx), `8000` (API), `5433` (Postgres expuesto por compose).
- Archivo `.env` en la raíz con variables obligatorias:
  - `DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/sgep_db` (en compose, host `db`)
  - `SECRET_KEY` (>= 32 caracteres, aleatoria y privada)
  - `ALLOWED_ORIGINS=https://tu-dominio` (o `http://IP:3000` según entorno)
  - Ajustar `EMAIL_ACTIVO`, `RATE_LIMIT_*`, `ALERTAS_INTERVALO_MINUTOS` según necesidad.

## 2. Despliegue con Docker (recomendado)
```bash
# En el servidor (raíz del repo)
cp .env.example .env   # editar valores reales
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
docker compose exec api python scripts/seed_demo.py   # opcional/idempotente
docker compose ps
```
- **Verificación**: `http://<host>:3000` carga SPA; `http://<host>:3000/api/v1/...` proxyea a API; `http://<host>:8000/health` -> healthy.
- **Migraciones**: se aplican automáticamente al iniciar la API (`alembic upgrade head` en lifespan).
- **Persistencia**: volúmenes `postgres_data` (BD) y `uploads_data` (PDFs). No borrar volúmenes en actualizaciones.

## 3. Actualización (siempre sincronizado con GitHub)
```bash
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
docker compose exec api python scripts/seed_demo.py   # idempotente
```
Ejecutar smoke rápido: login por rol, subir/evaluar evidencia, descarga y exportar CSV.

## 4. Despliegue sin Docker (alternativo)
1. PostgreSQL 16 activo y `DATABASE_URL` apuntando a él.
2. Backend: `uv sync --frozen --no-dev && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` (migraciones automáticas).
3. Frontend: `cd frontend && npm ci && npm run build` y servir `frontend/dist` con nginx (proxy `/api` -> `:8000`, fallback SPA a `index.html`, ver `frontend/nginx.conf`).
4. Seed opcional: `PYTHONPATH=. uv run python scripts/seed_demo.py`.

## 5. Backups y restauración
- **BD (Postgres, compose)**:
  - Backup: `docker compose exec -T db pg_dump -U postgres sgep_db > backup_sgep.sql`
  - Restore: `cat backup_sgep.sql | docker compose exec -T db psql -U postgres sgep_db`
- **Archivos PDF**: respaldar volumen `uploads_data` (`/app/uploads` en contenedor api).
- Programar respaldos periódicos y probar restauración antes de cierre formal.

## 6. Seguridad operativa
- `SECRET_KEY` única y privada; no commitear `.env`.
- Restringir `ALLOWED_ORIGINS` al dominio/IP real.
- Mantener `RATE_LIMIT_ENABLED=true` en auth; exponer solo puertos necesarios (ideal: 80/443 vía reverse proxy/TLS).
- Usuario no-root en contenedores (ya configurado en Dockerfile).

## 7. Checklist de cierre (fase 5)
- [x] Stack desplegable y reproducible (compose base + prod, scripts de arranque).
- [x] Migraciones automáticas y seed idempotente.
- [x] Credenciales demo y flujos RF02-RF07 validados (smokes/E2E).
- [x] Manual de usuario/capacitación disponible (`docs/MANUAL_USUARIO_CAPACITACION.md`).
- [x] Procedimiento de backup/restore y actualización documentado.
- [x] Repositorio GitHub actualizado para réplica en otros equipos.
