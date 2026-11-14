# Smokes pre-demo (SGEP)

Checklist rápido para validar antes de demo/despliegue. Ejecutar en local (SQLite) y/o Docker (Postgres).

## 0. Preparación
- [ ] `.env` con `SECRET_KEY` (>=32) y `DATABASE_URL` correcto para el entorno.
- [ ] Backend arriba (`http://localhost:8000/health` → healthy) y migraciones aplicadas.
- [ ] Frontend arriba (`http://localhost:5173` dev o `http://localhost:3000` Docker).

## 1. Flujo funcional (RF02–RF07)
- [ ] **RF02 Aprendiz**: login aprendiz demo, subir evidencia PDF, visible en “Mis evidencias”.
- [ ] **RF03/RF04 Instructor**: ver pendiente, evaluar (Aprobada/Ajuste) y registrar retroalimentación.
- [ ] **RF04 Aprendiz**: ver retroalimentación de su evidencia.
- [ ] **RF05 Coordinador**: crear/listar/eliminar asignación instructor↔aprendiz.
- [ ] **RF06 Aprendiz**: avance (%) coherente con evidencias aprobadas.
- [ ] **RF07 Coordinador**: dashboard y exportar CSV de expedientes/evidencias.

## 2. Seguridad y control de acceso
- [ ] **RBAC**: endpoints protegidos responden 401 sin token y 403 con rol indebido.
- [ ] **Descarga**: PDF solo accesible a dueño/instructor/coordinador autorizado (sin traversal).
- [ ] **Rate limit**: exceder intentos en auth devuelve 429 + `Retry-After`.
- [ ] **Refresh/logout**: rotación de refresh funcional; logout revoca e impide reutilización.

## 3. Calidad automatizada (gates)
- [ ] Backend: `uv run ruff check .` y `uv run pytest -q` (o `--cov=app --cov-fail-under=95`).
- [ ] Frontend: `cd frontend && npm run typecheck && npm test`.

## 4. Docker (Postgres) — cuando el daemon esté activo
- [ ] `docker compose up --build -d` (servicios healthy).
- [ ] `docker compose exec api python scripts/seed_demo.py`.
- [ ] Smoke UI en `http://localhost:3000` con credenciales demo de `README.md`.
- [ ] Confirmar paridad básica vs SQLite (login, CRUD evidencia, evaluación, CSV).

## 5. Evidencia de ejecución
- Registrar fecha, entorno (local/docker), commit, y resultado (OK/Falla + notas).


## 6. Ejecuci?n registrada (autom?tica/manual)
- **Fecha/entorno**: 2026-11-14 17:10 Hora est. Pacífico, Sudamérica ? local dev (SQLite, `DATABASE_URL=sqlite+aiosqlite:///./dev.db`) ? API `:8000`, front `:5173`.
- **Commit base**: `21e2a03` (previo a este registro; ver historial para commit de cierre).
- **Script**: `PYTHONPATH=. uv run python scripts/smoke_pre_demo.py` ? **TOTAL 20/20 OK** (health, login 3 roles, RF02 upload+visible, RF03/RF04 evaluar+retro, RF05 asignaciones, RF06 avance, RF07 dashboard+CSV, RBAC 401/403, descarga due?o/401, refresh rotaci?n+logout+reuse rechazada, rate limit 429).
- **Calidad**: `uv run ruff check .` OK ? `uv run pytest -q` 197 passed ? `frontend npm run typecheck` OK ? `npm test` 111 passed.
- **Docker E2E (Postgres, `:3000`)**: **PENDIENTE/BLOQUEADO** en esta m?quina (Docker daemon no disponible). Ejecutar con Docker activo: `docker compose up --build -d && docker compose exec api python scripts/seed_demo.py` y smoke UI en `http://localhost:3000`.
- **Notas**: seed demo aplicado en SQLite local; smoke de rate limit ejecutado al final (ventana agotada temporalmente durante la prueba).
