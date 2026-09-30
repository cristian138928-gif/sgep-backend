# tests/test_alertas_roles.py
"""
Tests de GET /instructor/alertas y GET /coordinador/alertas.
Cubre: alcance por asignacion, vista global, RBAC y validacion.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Coordinador, Evidencia, Instructor
from app.services.asignacion_service import AsignacionService
from app.services.auth_service import AuthService


# ====================================
# HELPERS
# ====================================

async def token_de(usuario) -> str:
    """Genera JWT para un usuario ya persistido."""
    return AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )


async def crear_instructor_bd(db_session) -> Instructor:
    """Crea un instructor en BD."""
    instructor = Instructor(
        nombre_completo="Instructor Alertas",
        correo_institucional="inst_alertas@test.com",
        numero_documento="1033333333",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Servicios Salud",
        especialidad="Software",
    )
    instructor.establecer_contrasena("InstPass123!")
    db_session.add(instructor)
    await db_session.commit()
    await db_session.refresh(instructor)
    return instructor


async def crear_aprendiz_bd(db_session, correo: str, numero_doc: str) -> Aprendiz:
    """Crea un aprendiz en BD con correo/documento unicos."""
    aprendiz = Aprendiz(
        nombre_completo=f"Aprendiz {correo.split('@')[0]}",
        correo_institucional=correo,
        numero_documento=numero_doc,
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha=numero_doc[-7:],
        programa="ADSO",
    )
    aprendiz.establecer_contrasena("Ap123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def crear_coordinador_bd(db_session) -> Coordinador:
    """Crea un coordinador en BD."""
    coordinador = Coordinador(
        nombre_completo="Coord Alertas Roles",
        correo_institucional="coord_roles@test.com",
        numero_documento="1055555556",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion",
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db_session.add(coordinador)
    await db_session.commit()
    await db_session.refresh(coordinador)
    return coordinador


async def crear_evidencia_bd(
    db_session,
    id_aprendiz: int,
    dias_limite: int,
    titulo: str = "Bitacora",
) -> Evidencia:
    """Crea una evidencia Pendiente con deadline relativo a hoy."""
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo=titulo,
        tipo_formato="Bitacora",
        ruta_archivo_pdf="uploads/roles.pdf",
        estado="Pendiente",
        fecha_deadline=datetime.now(timezone.utc) + timedelta(days=dias_limite),
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia


# ====================================
# TESTS: ALCANCE DEL INSTRUCTOR
# ====================================

@pytest.mark.asyncio
async def test_instructor_sin_asignaciones_lista_vacia(client: AsyncClient, db_session):
    """200: instructor sin aprendices asignados => lista vacia."""
    instructor = await crear_instructor_bd(db_session)

    response = await client.get(
        "/api/v1/instructor/alertas",
        headers={"Authorization": f"Bearer {await token_de(instructor)}"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_instructor_ve_alerta_de_su_aprendiz(client: AsyncClient, db_session):
    """200: alerta del aprendiz asignado, incluye nombre_aprendiz."""
    instructor = await crear_instructor_bd(db_session)
    aprendiz = await crear_aprendiz_bd(db_session, "propio@test.com", "1011111111")
    await AsignacionService.asignar(db_session, aprendiz.id_usuario, instructor.id_usuario)
    evidencia = await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=-1)

    response = await client.get(
        "/api/v1/instructor/alertas",
        headers={"Authorization": f"Bearer {await token_de(instructor)}"},
    )

    alertas = response.json()
    assert len(alertas) == 1
    assert alertas[0]["id_evidencia"] == evidencia.id_evidencia
    assert alertas[0]["estado_alerta"] == "Vencida"
    # EXPLICACIÓN: El rol supervisor necesita saber de QUIÉN es la evidencia
    assert alertas[0]["nombre_aprendiz"] == aprendiz.nombre_completo


@pytest.mark.asyncio
async def test_instructor_no_ve_aprendiz_sin_asignar(client: AsyncClient, db_session):
    """200: evidencia vencida de un aprendiz NO asignado no aparece."""
    instructor = await crear_instructor_bd(db_session)
    otro = await crear_aprendiz_bd(db_session, "otro@test.com", "1022222222")
    await crear_evidencia_bd(db_session, otro.id_usuario, dias_limite=-3)

    response = await client.get(
        "/api/v1/instructor/alertas",
        headers={"Authorization": f"Bearer {await token_de(instructor)}"},
    )

    assert response.json() == []


@pytest.mark.asyncio
async def test_instructor_no_ve_asignacion_desactivada(client: AsyncClient, db_session):
    """200: asignacion desactivada (activa=0) deja de generar alertas."""
    instructor = await crear_instructor_bd(db_session)
    aprendiz = await crear_aprendiz_bd(db_session, "desasig@test.com", "1033333334")
    await AsignacionService.asignar(db_session, aprendiz.id_usuario, instructor.id_usuario)
    await AsignacionService.desasignar(db_session, aprendiz.id_usuario)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=-1)

    response = await client.get(
        "/api/v1/instructor/alertas",
        headers={"Authorization": f"Bearer {await token_de(instructor)}"},
    )

    assert response.json() == []


# ====================================
# TESTS: VISTA GLOBAL DEL COORDINADOR
# ====================================

@pytest.mark.asyncio
async def test_coordinador_ve_alertas_de_todos_los_aprendices(
    client: AsyncClient, db_session
):
    """200: el coordinador no necesita asignacion; ve alertas globales."""
    aprendiz = await crear_aprendiz_bd(db_session, "global@test.com", "1044444444")
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=2)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=-1)
    coordinador = await crear_coordinador_bd(db_session)

    response = await client.get(
        "/api/v1/coordinador/alertas",
        headers={"Authorization": f"Bearer {await token_de(coordinador)}"},
    )

    alertas = response.json()
    assert len(alertas) == 2
    assert alertas[0]["estado_alerta"] == "Vencida"
    assert alertas[1]["estado_alerta"] == "Por vencer"
    assert alertas[0]["nombre_aprendiz"] == aprendiz.nombre_completo


@pytest.mark.asyncio
async def test_coordinador_ventana_de_dias(client: AsyncClient, db_session):
    """?dias=30 hace visible un deadline lejano solo para coordinador."""
    coordinador = await crear_coordinador_bd(db_session)

    aprendiz = await crear_aprendiz_bd(db_session, "ventana@test.com", "1077777777")
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=30)

    token = f"Bearer {await token_de(coordinador)}"
    assert len((await client.get("/api/v1/coordinador/alertas", headers={"Authorization": token})).json()) == 0
    assert len((await client.get("/api/v1/coordinador/alertas?dias=30", headers={"Authorization": token})).json()) == 1


# ====================================
# TESTS: RBAC Y VALIDACION
# ====================================

@pytest.mark.asyncio
async def test_aprendiz_no_accede_alertas_instructor_403(client: AsyncClient, db_session):
    """403: un aprendiz no puede consultar alertas de instructor."""
    aprendiz = await crear_aprendiz_bd(db_session, "rbac1@test.com", "1088888881")

    response = await client.get(
        "/api/v1/instructor/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_aprendiz_no_accede_alertas_coordinador_403(client: AsyncClient, db_session):
    """403: un aprendiz no puede consultar alertas de coordinacion."""
    aprendiz = await crear_aprendiz_bd(db_session, "rbac2@test.com", "1088888882")

    response = await client.get(
        "/api/v1/coordinador/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_alertas_dias_fuera_de_rango_422(client: AsyncClient, db_session):
    """422: ?dias=100 excede el limite permitido (le=90)."""
    instructor = await crear_instructor_bd(db_session)

    response = await client.get(
        "/api/v1/instructor/alertas?dias=100",
        headers={"Authorization": f"Bearer {await token_de(instructor)}"},
    )

    assert response.status_code == 422
