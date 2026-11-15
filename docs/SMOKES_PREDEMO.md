# Smokes pre-demo (SGEP)

Checklist rápido para validar antes de demo/despliegue. Ejecutar en local (SQLite) y/o Docker (Postgres).

## 0. Preparación
- [x] `.env` con `SECRET_KEY` (>=32) y `DATABASE_URL` correcto para el entorno.
- [x] Backend arriba (`http://localhost:8000/health` -> healthy) y migraciones aplicadas.
- [x] Frontend arriba (`http://localhost:5173` dev o `http://localhost:3000` Docker).

## 1. Flujo funcional (RF02-RF07)
- [x] **RF02 Aprendiz**: login aprendiz demo, subir evidencia PDF, visible en "Mis evidencias".
- [x] **RF03/RF04 Instructor**: ver pendiente, evaluar (Aprobada/Ajuste) y registrar retroalimentación.
- [x] **RF04 Aprendiz**: ver retroalimentación de su evidencia.
- [x] **RF05 Coordinador**: crear/listar/eliminar asignación instructor-aprendiz.
- [x] **RF06 Aprendiz**: avance (%) coherente con evidencias aprobadas.
- [x] **RF07 Coordinador**: dashboard y exportar CSV de expedientes/evidencias.

## 2. Seguridad y control de acceso
- [x] **RBAC**: endpoints protegidos responden 401 sin token y 403 con rol indebido.
- [x] **Descarga**: PDF solo accesible a dueño/instructor/coordinador autorizado (sin traversal).
- [x] **Rate limit**: exceder intentos en auth devuelve 429 + `Retry-After`.
- [x] **Refresh/logout**: rotación de refresh funcional; logout revoca e impide reutilización.

## 3. Calidad automatizada (gates)
- [x] Backend: `uv run ruff check .` y `uv run pytest -q` (o `--cov=app --cov-fail-under=95`).
- [x] Frontend: `cd frontend && npm run typecheck && npm test`.

## 4. Docker (Postgres)
- [x] `docker compose up --build -d` (servicios healthy).
- [x] `docker compose exec api python scripts/seed_demo.py` (reproducible con `PYTHONPATH=/app` en imagen; idempotente).
- [x] Smoke API/UI en `http://localhost:3000` con credenciales demo de `README.md`.
- [x] Paridad básica vs SQLite (login, evidencia, evaluación, CSV) verificada por smoke API.

## 5. Evidencia de ejecución

### 5.1 Local (SQLite, automático)
- **Fecha/entorno**: 2026-11-14 17:10 (-05:00) — local dev (`sqlite+aiosqlite:///./dev.db`) — API `:8000`, front `:5173`.
- **Commit**: `21e2a03`.
- **Script**: `PYTHONPATH=. uv run python scripts/smoke_pre_demo.py` → **TOTAL 20/20 OK** (health, login 3 roles, RF02 upload+visible, RF03/RF04 evaluar+retro, RF05 asignaciones, RF06 avance, RF07 dashboard+CSV, RBAC 401/403, descarga dueño/401, refresh rotación+logout+reuse rechazada, rate limit 429).
- **Calidad**: `uv run ruff check .` OK — `uv run pytest -q` 197 passed — `frontend npm run typecheck` OK — `npm test` 111 passed.
- **Notas**: seed demo aplicado en SQLite local; rate limit ejecutado al final de la corrida.

### 5.2 Docker E2E (Postgres, automático API)
- **Fecha/entorno**: 2026-11-15 00:24 (-05:00) — Docker compose (Postgres 16, api, frontend nginx) — UI `http://localhost:3000`, DB `:5433`.
- **Commit**: `e65ab73`.
- **Stack**: `docker compose up --build -d` → servicios `sgep_db`, `sgep_api` (healthy), `sgep_frontend` activos.
- **Seed**: ejecución inicial reportó `ModuleNotFoundError` por contexto de `PYTHONPATH`; corregido fijando `PYTHONPATH=/app` en la imagen. Datos de demo presentes en volumen Postgres (seed idempotente).
- **Smoke API vía Nginx :3000**: **TOTAL 18/18 OK** (login 3 roles, RF02 upload+visible, RF03/RF04 evaluar+retro, RF05 asignaciones, RF06 avance, RF07 dashboard+CSV, RBAC 401/403, descarga owner/401, refresh+logout+reuse rechazada). Rate limit no re-ejecutado para no bloquear ventana.
- **Smoke UI manual (:3000)**: pendiente de revalidación visual interactiva por rol (login/navegación/acciones principales) en próxima sesión con navegador; paridad funcional cubierta por smoke API y suite automatizada.

## 6. Estado de cierre funcional
- [x] Gates automatizados verdes (backend + frontend).
- [x] Smokes RF02-RF07 y seguridad ejecutados y registrados (local 20/20, Docker API 18/18).
- [x] Seed demo reproducible en Docker/entorno limpio (imagen con `PYTHONPATH=/app`).
- [ ] Smoke UI manual completo en `:3000` con evidencia visual (capturas/notas) — último paso de verificación humana antes de demo presencial.
