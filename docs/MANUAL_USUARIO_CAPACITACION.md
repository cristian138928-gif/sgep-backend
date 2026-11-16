# docs/MANUAL_USUARIO_CAPACITACION.md
# Manual de Usuario y Capacitación - SGEP

## 1. Acceso al sistema
- **URL**: `http://localhost:5173` (local dev) o `http://<host>:3000` (Docker/servidor).
- **Credenciales demo** (password `Demo1234!`): `aprendiz.demo@sena.edu.co`, `aprendiz2.demo@sena.edu.co`, `instructor.demo@sena.edu.co`, `coordinador.demo@sena.edu.co`.
- Inicio/cierre de sesión desde la pantalla de login; el perfil permite actualizar nombre, foto y contraseña.

## 2. Guía por rol

### Aprendiz
- **Avance (RF06)**: visualiza porcentaje de cumplimiento según evidencias aprobadas y alertas de vencimiento.
- **Mis evidencias (RF02)**: subir evidencia en PDF, consultar estado (Pendiente/Aprobada/Ajuste requerido) y ver retroalimentación del instructor (RF04).
- **Notificaciones**: revisar observaciones y avisos de vencimiento.

### Instructor
- **Bandeja de pendientes (RF03)**: listar evidencias por evaluar de aprendices asignados.
- **Evaluar (RF03/RF04)**: abrir evidencia, descargar PDF, marcar estado (Aprobada/Ajuste requerido) y registrar retroalimentación.
- **Historial**: consultar evaluaciones realizadas y estadísticas personales.

### Coordinador
- **Dashboard (RF07)**: métricas y estado global del proceso.
- **Aprendices/Evidencias/Bitácoras**: seguimiento y consulta consolidada.
- **Asignaciones (RF05)**: vincular o retirar instructor seguidor a aprendices.
- **Exportar CSV (RF07)**: descargar reporte de expedientes/avance.

## 3. Plan de capacitación sugerido (30-45 min)
1. **Introducción (5 min)**: objetivo del SGEP y flujo evidencia -> evaluación -> seguimiento.
2. **Demostración por rol (20 min)**: aprendiz sube y revisa avance; instructor evalúa y retroalimenta; coordinador asigna y exporta.
3. **Práctica guiada (10-15 min)**: cada usuario replica su flujo con datos demo.
4. **Cierre (5 min)**: resolución de dudas, buenas prácticas (PDF válido, revisión de notificaciones) y soporte.

## 4. Buenas prácticas y soporte
- Usar archivos PDF válidos y revisar el estado/retroalimentación tras cada evaluación.
- Si aparece bloqueo por intentos (429), esperar la ventana indicada o contactar al administrador.
- Ante inconvenientes: verificar sesión, recargar, y reportar con rol, hora y acción realizada.
- Administrador: ejecutar smoke (`scripts/smoke_pre_demo.py`) y revisar `/health`, logs `docker compose logs -f api`.

## 5. Acta de entrega y aceptación (plantilla)
- Fecha / versión (commit): __________________  Responsable: __________________
- Entorno entregado (URL/host): __________________  Usuarios capacitados: __________________
- Evidencia: demo de flujos RF02-RF07 completada [ ]  Documentación entregada [ ]
- Observaciones: ________________________________________________
- Firma aprendiz/responsable: __________  Firma instructor/cliente: __________
