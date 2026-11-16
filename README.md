# SGEP - Sistema de Gestión de Evidencias

API REST para gestionar evidencias de aprendices SENA durante su etapa práctica.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async)
- **DB**: PostgreSQL 16 (producción) / SQLite (tests)
- **Auth**: JWT (PyJWT)
- **Testing**: pytest + httpx + aiosqlite
- **DevOps**: Docker, docker-compose

## Quick Start

**Requisitos:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+. Copia `.env.example` a `.env` y define `SECRET_KEY` (>=32 chars). Por defecto usa SQLite local (`dev.db`, sin Docker).

**Arranque rápido (recomendado, auto-detecta Docker/local):**
```powershell
# Un solo comando: levanta servicios, espera healthchecks y (opcional) seed
.\scripts\start.ps1            # auto: Docker si el daemon está activo, si no local
.\scripts\start.ps1 -Mode docker  # fuerza Docker (:3000)
.\scripts\start.ps1 -Mode local -Seed  # fuerza local (:5173) + seed demo
```

**Despliegue/cierre (fase 5):** ver `docs/DESPLIEGUE_CIERRE.md`, `docs/MANUAL_USUARIO_CAPACITACION.md` y `.env.production.example` (`docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`).

```bash
# 1) Backend (migraciones se aplican al iniciar)
uv sync
uv run uvicorn app.main:app --reload --port 8000   # http://localhost:8000

# 2) Frontend (nueva terminal, proxy /api -> :8000)
cd frontend && npm install && npm run dev          # http://localhost:5173

# Tests
uv run pytest -q
cd frontend && npm run typecheck && npm test

# Docker (Postgres + API + Nginx en :3000; requiere Docker Desktop)
# Ajusta DATABASE_URL/credenciales según docker-compose.yml
docker compose up --build -d
docker compose exec api python scripts/seed_demo.py
```

## Demo en 1 minuto (presentación)

```bash
# 1. Levantar todo (migraciones se aplican solas al arrancar la api)
docker compose up --build -d

# 2. Sembrar datos de demo (idempotente: no pisa nada si ya existe)
docker compose exec api python scripts/seed_demo.py

# 3. Abrir la SPA
#    http://localhost:3000
```

| Rol | Correo | Password | Qué mostrar |
|---|---|---|---|
| Aprendiz | `aprendiz.demo@sena.edu.co` | `Demo1234!` | Avance **33.33%**, evidencia con ajuste |
| Aprendiz | `aprendiz2.demo@sena.edu.co` | `Demo1234!` | Avance **100%** (la "estrella") |
| Instructor | `instructor.demo@sena.edu.co` | `Demo1234!` | Bandeja, evaluar, historial |
| Coordinador | `coordinador.demo@sena.edu.co` | `Demo1234!` | Dashboard, CSV, asignaciones RF05 |

> **Nota**: `RATE_LIMIT_MAX` (defecto 10/min en auth) aplica también al demo. Si se
> dispara, esperar 60s o reiniciar `docker compose restart api`.

Verificaciones pre-presentación (smokes): flujo RF02→RF07 completo, seguridad
(RBAC 401/403, traversal, rate limit) y rotación de refresh tokens — todos pasan
en CI y localmente.

## Frontend (Vue 3 + TypeScript)

SPA en `frontend/` (Vite + Vue 3 + Pinia + Vue Router + TypeScript), estilos con Tailwind CSS v4 y tokens/clases centralizadas en `src/styles/ui-classes.ts` y `src/styles/main.css`.

```bash
cd frontend
npm install        # dependencias
npm run dev        # desarrollo con proxy /api -> http://localhost:8000
npm run typecheck  # vue-tsc --noEmit
npm test           # vitest (entorno happy-dom)
npm run build      # typecheck + build de producción en dist/
```

- **Tests**: `frontend/tests/*.spec.ts` cubren cliente HTTP (mutex del refresh, errores, `nombreSeguro`), JWT/session, stores, guards del router y montaje de vistas.
- **Auth**: cliente `fetch` propio (`src/api/client.ts`) con rotación de refresh tokens y mutex de reintento.
- **Guards**: rol leído del claim JWT (`meta.roles`); acceso indebido redirige al home del rol.
- **Vistas por rol**: aprendiz (avance + alertas + evidencias/RF04), instructor (bandeja + evaluar + historial), coordinador (dashboard + evidencias + aprendices/CSV + asignaciones RF05), notificaciones.
- **Descargas autenticadas**: PDFs y CSV vía `Authorization` y Blob.

## Calidad de Código

Dependencias Python: `uv` (`pyproject.toml` + `uv.lock`, fuente única; `requirements.txt` compatibilidad). Configuración en `pyproject.toml` (ruff + pytest + coverage):

```bash
uv run ruff check .            # lint (reglas E,F,W,I,UP,B,SIM,C4,RET,PIE,PTH)
uv run ruff check . --fix      # auto-fix seguro
uv run pytest --cov=app        # tests + cobertura (core=sysmon, Python 3.12+)
                               # CI exige >=95% (hoy 98%)
```

El frontend usa Vitest por separado (`cd frontend && npm test`); ambos jobs corren en GitHub Actions.

## Endpoints Principales

| Método | Ruta | Descripción | Rol |
|--------|------|-------------|-----|
| POST | /api/v1/auth/registro | Registro aprendiz | Público |
| POST | /api/v1/auth/registro-instructor | Registro instructor | Público |
| POST | /api/v1/auth/registro-coordinador | Registro coordinador | Público |
| POST | /api/v1/auth/login | Login (access + refresh) | Público |
| POST | /api/v1/auth/refresh | Canjear refresh token (rotación) | Público |
| POST | /api/v1/auth/logout | Revoca el refresh enviado (logout real) | Público (rate limit) |
| GET | /api/v1/auth/me | Perfil (nombre + rol) | Autenticado |
| PUT | /api/v1/auth/me | Editar nombre / cambiar contraseña (revoca refresh) | Autenticado |
| GET | /api/v1/notificaciones | Lista + badge no leídas | Autenticado |
| POST | /api/v1/notificaciones/marcar-todas-leidas | Acción masiva del header | Autenticado |
| POST | /api/v1/evidencias/upload | Subir PDF | Aprendiz |
| GET | /api/v1/evidencias/mis-evidencias | Mis evidencias | Aprendiz |
| GET | /api/v1/aprendiz/avance | Mi avance (%) | Aprendiz |
| GET | /api/v1/aprendiz/alertas?dias=7 | Alertas vencimiento | Aprendiz |
| GET | /api/v1/instructor/alertas?dias=7 | Vencimientos de sus aprendices | Instructor |
| GET | /api/v1/coordinador/alertas?dias=7 | Vencimientos globales | Coordinador |
| GET | /api/v1/evidencias/{id}/descarga | Descarga PDF seguro | Aprendiz/Instructor/Coord |
| GET | /api/v1/evidencias/{id}/retroalimentacion | Comentarios de la evidencia (RBAC) | Aprendiz dueño/Instructor/Coord |
| PUT | /api/v1/instructor/evaluar/{id} | Evaluar evidencia | Instructor |
| GET | /api/v1/instructor/evidencias-pendientes | Pendientes | Instructor |
| GET | /api/v1/instructor/historial | Historial paginado de evaluaciones | Instructor |
| GET | /api/v1/instructor/estadisticas | Métricas del instructor | Instructor |
| GET | /api/v1/instructor/perfil | Perfil del instructor | Instructor |
| GET | /api/v1/coordinador/estadisticas | Dashboard | Coordinador |
| GET | /api/v1/coordinador/evidencias | Todas las evidencias (paginadas) | Coordinador |
| GET | /api/v1/coordinador/aprendices | Aprendices con avance (paginado page/page_size) | Coordinador |
| GET | /api/v1/coordinador/instructores | Lista de instructores | Coordinador |
| GET | /api/v1/coordinador/exportar-avance | CSV consolidado de expedientes (RF07) | Coordinador |
| GET | /api/v1/coordinador/exportar-evidencias | CSV de evidencias | Coordinador |
| POST | /api/v1/retroalimentacion/ | Crear comentario independiente | Instructor |
| GET | /api/v1/retroalimentacion/{id} | Retroalimentación por ID (RBAC) | Dueño/Instructor/Coord |
| GET | /api/v1/asignaciones/ | Asignaciones activas (RF05) | Coordinador |
| POST | /api/v1/asignaciones/ | Asignar instructor seguidor (RF05) | Coordinador |
| DELETE | /api/v1/asignaciones/{id_aprendiz} | Quitar asignación (RF05) | Coordinador |
| GET | /api/v1/asignaciones/instructor/{id} | Aprendices de un instructor | Coordinador |
| GET | /api/v1/asignaciones/aprendiz/{id} | Instructor de un aprendiz | Coordinador/Aprendiz dueño |
| GET | /api/v1/notificaciones | Lista + badge no leídas | Autenticado |
| GET | /api/v1/notificaciones/no-leidas | Conteo de no leídas | Autenticado |
| POST | /api/v1/notificaciones/{id}/marcar-leida | Marcar una como leída | Autenticado |
| POST | /api/v1/notificaciones/marcar-todas-leidas | Acción masiva del header | Autenticado |

## Estructura

`
app/
├─ core/            # config (settings, fail-fast .env), dependencies (JWT/RBAC)
├─ db/              # sesión/engine async (session.py)
├─ api/routers/     # endpoints por dominio/rol
├─ models/          # SQLAlchemy (POO) + entidades
├─ schemas/         # Pydantic (validación/DTOs)
├─ services/        # lógica de negocio (auth, evidencias, email, notificaciones, etc.)
├─ security/        # rate limiting
└─ main.py          # FastAPI, CORS, cabeceras, lifespan (migraciones/alertas/purga)

tests/
├─ auth/            # auth, refresh, logout, perfil, rate limit
├─ evidencias/      # evidencias, retroalimentación, descargas, alertas
├─ gestion/         # aprendiz, instructor, coordinador, asignación, reportes, notificaciones
└─ core/            # config, conexión, email, main/lifespan, migraciones, modelos

frontend/            # SPA Vue 3 + TS + Vite + Tailwind v4 (src/api, router, stores, styles, views)
docs/                # documentación funcional/arquitectura y UI
scripts/             # utilidades (seed_demo.py)
alembic/             # migraciones
`

## Tests

`ash
# Backend (197 tests)
uv run pytest -q
# o con cobertura (CI exige >=95%)
uv run pytest --cov=app --cov-report=term --cov-fail-under=95 -q

# Frontend (111 tests)
cd frontend && npm test
`

## Seguridad

- **JWT doble**: `access` (24h, autoriza API) + `refresh` (7d, solo canjea en `/auth/refresh` con rotación).
- **Logout real**: `POST /auth/logout` borra el `jti` del refresh en BD (idempotente; la SPA lo llama antes de limpiar localStorage).
- **Purga de caducados**: tarea en `lifespan` (`REFRESH_PURGA_INTERVALO_MINUTOS`, 60 en compose) que borra `refresh_tokens` vencidos.
- **Rate limiting**: ventana deslizante en endpoints públicos → `429` + `Retry-After` (configurable con `RATE_LIMIT_*`).
- **Fail-fast de entorno**: `app/core/config.py` valida `.env` al importar y lista todos los errores de una vez.
- **Cabeceras OWASP**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` en toda respuesta.
- **RBAC**: 3 roles con verificación por endpoint; descarga de PDFs con validación de propiedad.

## Reportes y Notificaciones

- **RF07**: `GET /coordinador/exportar-avance` → CSV de expedientes (avance % por aprendiz) con quoting correcto vía `csv` module.
- **Notificaciones in-app**: se crean al evaluar una evidencia y al acercarse fechas límite (tarea `lifespan` cada `ALERTAS_INTERVALO_MINUTOS`, con dedupe).
- **Email transaccional**: `BackgroundTasks` post-respuesta; con `EMAIL_ACTIVO=false` solo loguea (dev/tests), con SMTP real en producción.

## Variables de Entorno

Copia `.env.example` a `.env`. Obligatorias: `DATABASE_URL` y `SECRET_KEY` (≥32 caracteres).

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sgep_db
SECRET_KEY=tu_clave_secreta_minimo_32_caracteres
ALGORITHM=HS256
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate limiting (intentos por ventana y ruta/IP)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW=60

# Coste bcrypt (los tests lo bajan a 4 solos)
BCRYPT_ROUNDS=12

# Email + alertas programadas
EMAIL_ACTIVO=false
ALERTAS_INTERVALO_MINUTOS=0
```
