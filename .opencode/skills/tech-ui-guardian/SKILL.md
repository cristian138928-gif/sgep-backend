---
name: tech-ui-guardian
description: Use when improving SGEP UI/UX to be professional, technological and modern, or when reviewing/updating frontend stack, dependencies and practices to stay current. Trigger on requests about interfaz, frontend, diseño moderno, actualización tecnológica, mantener al día, UI polish.
---

# Tech UI Guardian (SGEP)

## Propósito
- Mantener la interfaz profesional, tecnológica y moderna sin romper flujos, rutas, stores ni contratos API existentes.
- Mantener el stack y prácticas al día de forma segura y verificable.

## Reglas UI/Frontend
- Respetar invariantes de `AGENTS.md` y tokens/clases en `src/styles/ui-classes.ts` y `src/styles/main.css` (no reescribir lógica de negocio por estilo).
- Priorizar: jerarquía clara, contraste/accesibilidad, consistencia enterprise (slate/emerald), microinteracciones sutiles, rendimiento.
- Cambios incrementales y compatibles: preservar nombres de clases usadas por vistas, props/emit y comportamiento.
- Evitar dependencias nuevas innecesarias; preferir CSS/variables y componentes existentes.

## Mantener al día (checklist)
- Revisar versiones en `frontend/package.json`, `pyproject.toml`, `Dockerfile`, workflows CI; proponer actualizaciones menores/patch seguras.
- Verificar compatibilidad antes de subir majors; nunca romper build/tests.
- Validar tras cambios: `uv run ruff check .`, `uv run pytest -q`, `cd frontend && npm run typecheck && npm test && npm run build`.

## Entrega
- Resumir cambios y riesgos; si hay updates disponibles, listar impacto y plan.
- Siempre dejar repo listo para `git pull` (commit/push de cambios coherentes).
