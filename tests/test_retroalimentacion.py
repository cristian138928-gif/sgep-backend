# tests/test_retroalimentacion.py
"""
Tests para endpoints de retroalimentacion independiente.
Cubre: crear con/ sin cambio de estado, obtener por ID, por evidencia, seguridad.
"""

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Evidencia, Instructor
from app.services.auth_service import AuthService

# ====================================
# HELPERS
# ====================================

async def crear_instructor_token(db_session) -> tuple[str, Instructor]:
    """Crea instructor y retorna (JWT, objeto)."""
    inst = Instructor(
        nombre_completo="Instructor Retro",
        correo_institucional="inst_retro@test.com",
        numero_documento="1055555555",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Tech",
        especialidad="Software"
    )
    inst.establecer_contrasena("Inst123!")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    token = AuthService.crear_token_acceso(
        data={"sub": inst.correo_institucional, "id": inst.id_usuario}
    )
    return token, inst


async def crear_aprendiz_con_evidencia(
    db_session, estado="Pendiente"
) -> tuple[Aprendiz, Evidencia]:
    """Crea aprendiz + evidencia y retorna ambos."""
    ap = Aprendiz(
        nombre_completo="Aprendiz Retro",
        correo_institucional="ap_retro@test.com",
        numero_documento="1066666666",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="666",
        programa="ADSO"
    )
    ap.establecer_contrasena("Ap123!")
    db_session.add(ap)
    await db_session.commit()
    await db_session.refresh(ap)

    ev = Evidencia(
        id_aprendiz=ap.id_usuario,
        titulo="Bitacora Test Retro",
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test/retro.pdf",
        estado=estado
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)
    return ap, ev


# ====================================
# TESTS - CREAR RETROALIMENTACION
# ====================================

@pytest.mark.asyncio
async def test_crear_retroalimentacion_solo_comentario(client: AsyncClient, db_session):
    """Test: Crear retroalimentacion sin cambiar estado."""
    token, instructor = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "Comentario de prueba para la bitacora del aprendiz"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id_evidencia"] == evidencia.id_evidencia
    assert data["id_instructor"] == instructor.id_usuario
    assert "Comentario de prueba" in data["observaciones"]
    assert data["estado_evaluacion"] == "Pendiente"  # No cambio


@pytest.mark.asyncio
async def test_crear_retroalimentacion_con_estado(client: AsyncClient, db_session):
    """Test: Crear retroalimentacion cambiando estado a Aprobada."""
    token, instructor = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "Evidencia aprobada por cumplir requisitos minimos",
            "estado_evaluacion": "Aprobada"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["estado_evaluacion"] == "Aprobada"


@pytest.mark.asyncio
async def test_crear_retroalimentacion_ajuste(client: AsyncClient, db_session):
    """Test: Crear retroalimentacion con ajuste requerido."""
    token, instructor = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "La bitacora no cumple con el formato requerido, ajuste necesario",
            "estado_evaluacion": "Ajuste Requerido"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["estado_evaluacion"] == "Ajuste Requerido"


@pytest.mark.asyncio
async def test_crear_retroalimentacion_evidencia_no_existe(client: AsyncClient, db_session):
    """Test: Evidencia inexistente -> 404."""
    token, _ = await crear_instructor_token(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": 99999,
            "observaciones": "Comentario para evidencia que no existe en el sistema"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_crear_retroalimentacion_observaciones_cortas(client: AsyncClient, db_session):
    """Test: Observaciones muy cortas -> 422."""
    token, _ = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "Corto"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# ====================================
# TESTS - OBTENER RETROALIMENTACION
# ====================================

@pytest.mark.asyncio
async def test_obtener_retroalimentacion_por_id(client: AsyncClient, db_session):
    """Test: Obtener retroalimentacion por su ID."""
    token, instructor = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    # Crear
    create_resp = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "Comentario para buscar por ID posteriormente"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    retro_id = create_resp.json()["id_retroalimentacion"]

    # Obtener por ID
    response = await client.get(
        f"/api/v1/retroalimentacion/{retro_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["id_retroalimentacion"] == retro_id


@pytest.mark.asyncio
async def test_obtener_retroalimentacion_por_evidencia(client: AsyncClient, db_session):
    """Test: Obtener retroalimentacion de una evidencia."""
    token, instructor = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "Comentario para buscar por evidencia especifica"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get(
        f"/api/v1/retroalimentacion/evidencia/{evidencia.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["id_evidencia"] == evidencia.id_evidencia


@pytest.mark.asyncio
async def test_obtener_retroalimentacion_no_existe(client: AsyncClient, db_session):
    """Test: Retroalimentacion inexistente -> 404."""
    token, _ = await crear_instructor_token(db_session)

    response = await client.get(
        "/api/v1/retroalimentacion/99999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_obtener_retroalimentacion_evidencia_sin_retro(client: AsyncClient, db_session):
    """Test: Evidencia sin retroalimentacion -> 404."""
    token, _ = await crear_instructor_token(db_session)
    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.get(
        f"/api/v1/retroalimentacion/evidencia/{evidencia.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


# ====================================
# TESTS - SEGURIDAD
# ====================================

@pytest.mark.asyncio
async def test_aprendiz_no_puede_crear_retroalimentacion(client: AsyncClient, db_session):
    """Test: Aprendiz no puede crear retroalimentacion -> 403."""
    ap, evidencia = await crear_aprendiz_con_evidencia(db_session)
    token_ap = AuthService.crear_token_acceso(
        data={"sub": ap.correo_institucional, "id": ap.id_usuario}
    )

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "El aprendiz no deberia poder comentar su propia evidencia"
        },
        headers={"Authorization": f"Bearer {token_ap}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_coordinador_no_puede_crear_retroalimentacion(client: AsyncClient, db_session):
    """Test: Coordinador no puede crear retroalimentacion -> 403."""
    from app.models.usuario import Coordinador

    coord = Coordinador(
        nombre_completo="Coord Test",
        correo_institucional="coord_retro@test.com",
        numero_documento="1077777777",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Academica"
    )
    coord.establecer_contrasena("Coord123!")
    db_session.add(coord)
    await db_session.commit()
    await db_session.refresh(coord)

    token = AuthService.crear_token_acceso(
        data={"sub": coord.correo_institucional, "id": coord.id_usuario}
    )

    _, evidencia = await crear_aprendiz_con_evidencia(db_session)

    response = await client.post(
        "/api/v1/retroalimentacion/",
        json={
            "id_evidencia": evidencia.id_evidencia,
            "observaciones": "El coordinador no deberia poder crear retroalimentacion directamente"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
