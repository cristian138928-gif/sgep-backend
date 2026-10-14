# tests/test_asignacion.py
"""
Tests para endpoints de asignacion de seguimiento.
Cubre: crear, desasignar, listar, seguridad.
"""

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Coordinador, Instructor
from app.services.auth_service import AuthService

# ====================================
# HELPERS
# ====================================

async def crear_coordinador_token(db_session) -> str:
    """Crea coordinador y retorna JWT."""
    coord = Coordinador(
        nombre_completo="Coord Test",
        correo_institucional="coord@test.com",
        numero_documento="1099999999",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Academica"
    )
    coord.establecer_contrasena("Coord123!")
    db_session.add(coord)
    await db_session.commit()
    await db_session.refresh(coord)
    return AuthService.crear_token_acceso(
        data={"sub": coord.correo_institucional, "id": coord.id_usuario}
    )


async def crear_instructor(db_session, email="inst@test.com") -> Instructor:
    """Crea instructor en BD."""
    inst = Instructor(
        nombre_completo="Instructor Test",
        correo_institucional=email,
        numero_documento="10" + str(hash(email))[:8],
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software"
    )
    inst.establecer_contrasena("Inst123!")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    return inst


async def crear_aprendiz(db_session, email="ap@test.com", ficha="111") -> Aprendiz:
    """Crea aprendiz en BD."""
    ap = Aprendiz(
        nombre_completo="Aprendiz Test",
        correo_institucional=email,
        numero_documento="10" + str(hash(email))[:8],
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha=ficha,
        programa="ADSO"
    )
    ap.establecer_contrasena("Ap123!")
    db_session.add(ap)
    await db_session.commit()
    await db_session.refresh(ap)
    return ap


# ====================================
# TESTS - CREAR ASIGNACION
# ====================================

@pytest.mark.asyncio
async def test_crear_asignacion(client: AsyncClient, db_session):
    """Test: Asignar aprendiz a instructor."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id_aprendiz"] == aprendiz.id_usuario
    assert data["id_instructor"] == instructor.id_usuario
    assert data["activa"] is True
    assert data["nombre_aprendiz"] == "Aprendiz Test"
    assert data["nombre_instructor"] == "Instructor Test"


@pytest.mark.asyncio
async def test_crear_asignacion_aprendiz_no_existe(client: AsyncClient, db_session):
    """Test: Asignar aprendiz inexistente -> 404."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)

    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": 99999, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_crear_asignacion_instructor_no_existe(client: AsyncClient, db_session):
    """Test: Asignar instructor inexistente -> 404."""
    token = await crear_coordinador_token(db_session)
    aprendiz = await crear_aprendiz(db_session)

    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": 99999},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_crear_asignacion_duplicada(client: AsyncClient, db_session):
    """Test: Aprendiz ya tiene asignacion activa -> 409."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    # Primera asignacion
    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Intentar duplicar
    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 409


# ====================================
# TESTS - DESASIGNAR
# ====================================

@pytest.mark.asyncio
async def test_desasignar(client: AsyncClient, db_session):
    """Test: Desasignar aprendiz de instructor."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    # Asignar primero
    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Desasignar
    response = await client.delete(
        f"/api/v1/asignaciones/{aprendiz.id_usuario}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "desactivada" in response.json()["mensaje"]


@pytest.mark.asyncio
async def test_desasignar_no_existe(client: AsyncClient, db_session):
    """Test: Desasignar aprendiz sin asignacion -> 404."""
    token = await crear_coordinador_token(db_session)

    response = await client.delete(
        "/api/v1/asignaciones/99999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


# ====================================
# TESTS - LISTAR APRENDICES DEL INSTRUCTOR
# ====================================

@pytest.mark.asyncio
async def test_listar_aprendices_instructor(client: AsyncClient, db_session):
    """Test: Lista aprendices asignados a un instructor."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    ap1 = await crear_aprendiz(db_session, email="ap1@test.com", ficha="111")
    ap2 = await crear_aprendiz(db_session, email="ap2@test.com", ficha="222")

    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": ap1.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )
    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": ap2.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get(
        f"/api/v1/asignaciones/instructor/{instructor.id_usuario}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_listar_aprendices_instructor_vacio(client: AsyncClient, db_session):
    """Test: Instructor sin aprendices -> lista vacia."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)

    response = await client.get(
        f"/api/v1/asignaciones/instructor/{instructor.id_usuario}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


# ====================================
# TESTS - VER INSTRUCTOR ASIGNADO
# ====================================

@pytest.mark.asyncio
async def test_ver_instructor_asignado(client: AsyncClient, db_session):
    """Test: Aprendiz ve su instructor asignado."""
    token_coord = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token_coord}"}
    )

    # Token del aprendiz
    token_ap = AuthService.crear_token_acceso(
        data={"sub": aprendiz.correo_institucional, "id": aprendiz.id_usuario}
    )

    response = await client.get(
        f"/api/v1/asignaciones/aprendiz/{aprendiz.id_usuario}",
        headers={"Authorization": f"Bearer {token_ap}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id_instructor"] == instructor.id_usuario
    assert data["nombre_instructor"] == "Instructor Test"


@pytest.mark.asyncio
async def test_ver_instructor_no_asignado(client: AsyncClient, db_session):
    """Test: Aprendiz sin asignacion -> 404."""
    aprendiz = await crear_aprendiz(db_session)

    token_ap = AuthService.crear_token_acceso(
        data={"sub": aprendiz.correo_institucional, "id": aprendiz.id_usuario}
    )

    response = await client.get(
        f"/api/v1/asignaciones/aprendiz/{aprendiz.id_usuario}",
        headers={"Authorization": f"Bearer {token_ap}"}
    )

    assert response.status_code == 404


# ====================================
# TESTS - SEGURIDAD
# ====================================

@pytest.mark.asyncio
async def test_aprendiz_no_puede_crear_asignacion(client: AsyncClient, db_session):
    """Test: Aprendiz no puede crear asignaciones -> 403."""
    aprendiz = await crear_aprendiz(db_session)
    instructor = await crear_instructor(db_session)

    token = AuthService.crear_token_acceso(
        data={"sub": aprendiz.correo_institucional, "id": aprendiz.id_usuario}
    )

    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_instructor_no_puede_crear_asignacion(client: AsyncClient, db_session):
    """Test: Instructor no puede crear asignaciones -> 403."""
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    token = AuthService.crear_token_acceso(
        data={"sub": instructor.correo_institucional, "id": instructor.id_usuario}
    )


    response = await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


# ====================================
# TESTS - RF05: LISTADO GLOBAL (COORDINADOR)
# ====================================

@pytest.mark.asyncio
async def test_listar_asignaciones_coordinador(client: AsyncClient, db_session):
    """Test: GET /asignaciones/ devuelve la asignacion activa con ambos nombres."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get(
        "/api/v1/asignaciones/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre_aprendiz"] == "Aprendiz Test"
    assert data[0]["nombre_instructor"] == "Instructor Test"
    assert data[0]["activa"] is True


@pytest.mark.asyncio
async def test_listar_asignaciones_excluye_desactivadas(client: AsyncClient, db_session):
    """Test: la asignacion quitada con DELETE no aparece en la lista."""
    token = await crear_coordinador_token(db_session)
    instructor = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    await client.post(
        "/api/v1/asignaciones/",
        json={"id_aprendiz": aprendiz.id_usuario, "id_instructor": instructor.id_usuario},
        headers={"Authorization": f"Bearer {token}"}
    )
    await client.delete(
        f"/api/v1/asignaciones/{aprendiz.id_usuario}",
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get(
        "/api/v1/asignaciones/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_listar_asignaciones_rol_no_autorizado(client: AsyncClient, db_session):
    """Test: instructor y aprendiz no ven el listado -> 403."""
    token_ins = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)

    for token in (
        AuthService.crear_token_acceso(
            data={"sub": token_ins.correo_institucional, "id": token_ins.id_usuario}
        ),
        AuthService.crear_token_acceso(
            data={"sub": aprendiz.correo_institucional, "id": aprendiz.id_usuario}
        ),
    ):
        response = await client.get(
            "/api/v1/asignaciones/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
