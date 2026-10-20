# SGEP - Sistema de Gestión de Evidencias

API REST para gestionar evidencias de aprendices SENA durante su etapa práctica.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async)
- **DB**: PostgreSQL 16 (producción) / SQLite (tests)
- **Auth**: JWT (PyJWT)
- **Testing**: pytest + httpx + aiosqlite
- **DevOps**: Docker, docker-compose

## Quick Start

```bash
# Instalar dependencias (uv resuelve desde pyproject.toml)
uv sync

# Ejecutar tests
uv run pytest tests/ -v

# Ejecutar API
uv run uvicorn app.main:app --reload --port 8000

# Frontend (SPA Vue 3, proxy /api -> :8000)
cd frontend && npm install && npm run dev   # http://localhost:5173

# Migraciones (Alembic)
uv run alembic revision --autogenerate -m "descripcion"   # generar desde modelos
uv run alembic upgrade head                               # aplicar
uv run alembic downgrade -1                               # retroceder una revisión

# Docker (producción local: db + api + frontend en :3000, migraciones solas al arrancar)
docker compose up --build -d

# Docker desarrollo (hot reload: editas app/*.py y uvicorn recarga solo)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Frontend (Vue 3 + TypeScript)

SPA en `frontend/` construida con Vite, tipada con `vue-tsc` y sin framework CSS (tokens propios en `src/styles/main.css`).

```bash
cd frontend
npm install        # dependencias (vue, vue-router, pinia, vite)
npm run dev        # desarrollo con proxy /api -> http://localhost:8000
npm run typecheck  # vue-tsc --noEmit
npm run build      # typecheck + build de producción en dist/
```

- **Auth**: cliente `fetch` propio (`src/api/client.ts`) con rotación de refresh tokens y mutex de reintento (un solo refresh ante N peticiones en 401).
- **Guards**: rol leído del claim JWT del token (`meta.roles` en rutas); acceso equivocado redirige al home del propio rol.
- **Vistas por rol**: aprendiz (avance + alertas + evidencias con retroalimentación RF04), instructor (bandeja + evaluar + historial), coordinador (dashboard + evidencias con filtros + aprendices con CSV + asignaciones RF05), notificaciones para los 3 roles.
- **Descargas autenticadas**: PDFs y CSV se solicitan con `Authorization` y se guardan vía Blob.

## Calidad de Código

Configuración única en `pyproject.toml` (ruff + pytest + coverage):

```bash
uv run ruff check .            # lint (reglas E,F,W,I,UP,B,SIM,C4,RET,PIE,PTH)
uv run ruff check . --fix      # auto-fix seguro
uv run pytest --cov=app        # tests + cobertura (core=sysmon, Python 3.12+)
```

## Endpoints Principales

| Método | Ruta | Descripción | Rol |
|--------|------|-------------|-----|
| POST | /api/v1/auth/registro | Registro aprendiz | Público |
| POST | /api/v1/auth/registro-instructor | Registro instructor | Público |
| POST | /api/v1/auth/registro-coordinador | Registro coordinador | Público |
| POST | /api/v1/auth/login | Login (access + refresh) | Público |
| POST | /api/v1/auth/refresh | Canjear refresh token (rotación) | Público |
| GET | /api/v1/auth/me | Perfil (nombre + rol) | Autenticado |
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
| GET | /api/v1/coordinador/aprendices | Aprendices con avance | Coordinador |
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

```
app/
├── main.py              # Entry point FastAPI + CORS + cabeceras OWASP + lifespan alertas
├── config.py            # Settings tipados + validación fail-fast de .env
├── models/usuario.py    # SQLAlchemy models (POO) + Notificacion
├── routes/              # Endpoints por rol (+ notificaciones + retroalimentación)
├── schemas/             # Pydantic validation (ConfigDict v2)
├── security/            # Rate limiting (ventana deslizante)
├── services/            # Business logic (+ email, notificaciones)
├── dependencies.py      # JWT auth (PyJWT, claims type=access/refresh)
└── database/            # Connection config
tests/
├── conftest.py          # Fixtures + helpers
├── test_auth.py         # 18 tests
├── test_config.py       # 4 tests (validación de .env)
├── test_refresh.py      # 6 tests (rotación de tokens)
├── test_rate_limit.py   # 5 tests (429 + cabeceras OWASP)
├── test_notificaciones.py # 9 tests (in-app + dedupe de vencimientos)
├── test_email.py        # 3 tests (consola + SMTP fake)
├── test_reportes.py     # 3 tests (CSV expedientes RF07)
├── test_evidencias.py   # 9 tests
├── test_instructor.py   # 16 tests
├── test_coordinador.py  # 13 tests
├── test_asignacion.py   # 15 tests (incluye listado global RF05)
├── test_retroalimentacion.py # 17 tests (incluye RBAC de lectura RF04)
├── test_aprendiz.py     # 3 tests
├── test_descarga.py     # 8 tests
├── test_alertas.py      # 9 tests
├── test_alertas_roles.py # 9 tests
├── test_main.py         # 4 tests (lifespan + cabeceras)
├── test_models_poo.py   # 15 tests (herencia/polimorfismo)
└── test_connection.py   # 1 test
```

## Tests

```bash
# Todos los tests (167)
uv run pytest tests/ -v

# Solo auth
uv run pytest tests/test_auth.py -v

# Con coverage (98%)
uv run pytest tests/ --cov=app
```

## Seguridad

- **JWT doble**: `access` (24h, autoriza API) + `refresh` (7d, solo canjea en `/auth/refresh` con rotación).
- **Rate limiting**: ventana deslizante en endpoints públicos → `429` + `Retry-After` (configurable con `RATE_LIMIT_*`).
- **Fail-fast de entorno**: `app/config.py` valida `.env` al importar y lista todos los errores de una vez.
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
