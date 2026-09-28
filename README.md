# SGEP - Sistema de Gestión de Evidencias

API REST para gestionar evidencias de aprendices SENA durante su etapa práctica.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async)
- **DB**: PostgreSQL 16 (producción) / SQLite (tests)
- **Auth**: JWT (python-jose)
- **Testing**: pytest + httpx + aiosqlite
- **DevOps**: Docker, docker-compose

## Quick Start

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
pytest tests/ -v

# Ejecutar API
uvicorn app.main:app --reload --port 8000

# Docker
docker-compose up --build
```

## Endpoints Principales

| Método | Ruta | Descripción | Rol |
|--------|------|-------------|-----|
| POST | /api/v1/auth/registro | Registro aprendiz | Público |
| POST | /api/v1/auth/registro-instructor | Registro instructor | Público |
| POST | /api/v1/auth/registro-coordinador | Registro coordinador | Público |
| POST | /api/v1/auth/login | Login | Público |
| POST | /api/v1/evidencias/upload | Subir PDF | Aprendiz |
| GET | /api/v1/evidencias/mis-evidencias | Mis evidencias | Aprendiz |
| GET | /api/v1/aprendiz/avance | Mi avance (%) | Aprendiz |
| PUT | /api/v1/instructor/evaluar/{id} | Evaluar evidencia | Instructor |
| GET | /api/v1/instructor/evidencias-pendientes | Pendientes | Instructor |
| GET | /api/v1/coordinador/estadisticas | Dashboard | Coordinador |
| GET | /api/v1/coordinador/evidencias | Todas las evidencias | Coordinador |

## Estructura

```
app/
├── main.py              # Entry point FastAPI
├── models/usuario.py    # SQLAlchemy models (POO)
├── routes/              # Endpoints por rol
├── schemas/             # Pydantic validation
├── services/            # Business logic
├── dependencies.py      # JWT auth
└── database/            # Connection config
tests/
├── conftest.py          # Fixtures + helpers
├── test_auth.py         # 12 tests
├── test_evidencias.py   # 4 tests
├── test_instructor.py   # 10 tests
├── test_coordinador.py  # 12 tests
├── test_asignacion.py   # 12 tests
├── test_retroalimentacion.py # 8 tests
└── test_aprendiz.py     # 3 tests
```

## Tests

```bash
# Todos los tests (67)
pytest tests/ -v

# Solo auth
pytest tests/test_auth.py -v

# Con coverage
pytest tests/ --cov=app
```

## Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sgep_db
SECRET_KEY=tu_clave_secreta_minimo_32_caracteres
ALGORITHM=HS256
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```
