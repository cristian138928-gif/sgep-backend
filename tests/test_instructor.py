# tests/test_instructor.py
"""
Tests para endpoints del instructor.
Cubre: perfil, estadisticas, evaluar, historial.
"""

import pytest
from httpx import AsyncClient


# ====================================
# HELPERS
# ====================================

async def crear_instructor(db_session):
    """Crea un instructor en BD y retorna su token."""
    from app.models.usuario import Instructor
    from app.services.auth_service import AuthService

    instructor = Instructor(
        nombre_completo="Instructor Test",
        correo_institucional="instructor@test.com",
        numero_documento="1088888888",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro de Salud",
        especialidad="Desarrollo de Software"
    )
    instructor.establecer_contrasena("InstrPass123!")
    db_session.add(instructor)
    await db_session.commit()
    await db_session.refresh(instructor)

    return AuthService.crear_token_acceso(
        data={"sub": instructor.correo_institucional, "id": instructor.id_usuario}
    )


async def crear_aprendiz(db_session, email="aprendiz@test.com"):
    """Crea un aprendiz en BD."""
    from app.models.usuario import Aprendiz

    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Test",
        correo_institucional=email,
        numero_documento="1077777777",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="1111111",
        programa="ADSO"
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def crear_evidencia_pendiente(db_session, id_aprendiz):
    """Crea una evidencia pendiente."""
    from app.models.usuario import Evidencia

    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo="Bitacora Pendiente",
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test.pdf",
        estado="Pendiente"
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia


# ====================================
# TESTS - PERFIL
# ====================================

@pytest.mark.asyncio
async def test_mi_perfil(client: AsyncClient, db_session):
    """Test: GET /api/v1/instructor/perfil"""
    token = await crear_instructor(db_session)

    response = await client.get(
        "/api/v1/instructor/perfil",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nombre_completo"] == "Instructor Test"
    assert data["centro_formacion"] == "Centro de Salud"
    assert data["especialidad"] == "Desarrollo de Software"


# ====================================
# TESTS - ESTADISTICAS
# ====================================

@pytest.mark.asyncio
async def test_estadisticas_vacias(client: AsyncClient, db_session):
    """Test: Estadisticas del instructor vacias."""
    token = await crear_instructor(db_session)

    response = await client.get(
        "/api/v1/instructor/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluadas"] == 0
    assert data["aprobadas"] == 0
    assert data["pendientes_por_evaluar"] == 0


@pytest.mark.asyncio
async def test_estadisticas_con_evaluaciones(client: AsyncClient, db_session):
    """Test: Estadisticas con evaluaciones previas."""
    instructor_id = (await crear_instructor(db_session))
    token = instructor_id
    aprendiz = await crear_aprendiz(db_session)

    # Crear evidencia y evaluarla
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    # Decodificar token para obtener ID
    from jose import jwt
    from dotenv import load_dotenv
    import os
    load_dotenv()
    payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
    instructor_id_num = payload["id"]

    from app.models.usuario import Retroalimentacion
    retro = Retroalimentacion(
        id_evidencia=ev.id_evidencia,
        id_instructor=instructor_id_num,
        observaciones="Evaluacion de prueba",
        estado_evaluacion="Aprobada"
    )
    db_session.add(retro)
    await db_session.commit()

    response = await client.get(
        "/api/v1/instructor/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluadas"] == 1
    assert data["aprobadas"] == 1


# ====================================
# TESTS - EVIDENCIAS PENDIENTES
# ====================================

@pytest.mark.asyncio
async def test_evidencias_pendientes(client: AsyncClient, db_session):
    """Test: GET /api/v1/instructor/evidencias-pendientes"""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    response = await client.get(
        "/api/v1/instructor/evidencias-pendientes",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


# ====================================
# TESTS - EVALUAR
# ====================================

@pytest.mark.asyncio
async def test_evaluar_aprobar(client: AsyncClient, db_session):
    """Test: PUT /api/v1/instructor/evaluar/{id} - Aprobar"""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    response = await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "estado": "Aprobada",
            "observaciones": "Excelente bitacora, cumple todos los requisitos."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estado_evaluacion"] == "Aprobada"


@pytest.mark.asyncio
async def test_evaluar_ajuste(client: AsyncClient, db_session):
    """Test: PUT /api/v1/instructor/evaluar/{id} - Ajuste Requerido"""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    response = await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "estado": "Ajuste Requerido",
            "observaciones": "Faltan imagenes en la bitacora. Por favor agregar screenshots."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estado_evaluacion"] == "Ajuste Requerido"


@pytest.mark.asyncio
async def test_evaluar_estado_invalido(client: AsyncClient, db_session):
    """Test: Evaluar con estado invalido."""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    response = await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "estado": "Invalido",
            "observaciones": "Esto no deberia funcionar."
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_evaluar_ya_evaluada(client: AsyncClient, db_session):
    """Test: Evaluar evidencia ya evaluada."""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    # Primera evaluacion
    await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={"estado": "Aprobada", "observaciones": "Primera evaluacion correcta."}
    )

    # Segunda evaluacion (debe fallar)
    response = await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={"estado": "Aprobada", "observaciones": "Segunda evaluacion no deberia funcionar."}
    )

    assert response.status_code == 409


# ====================================
# TESTS - HISTORIAL
# ====================================

@pytest.mark.asyncio
async def test_historial_vacio(client: AsyncClient, db_session):
    """Test: Historial vacio del instructor."""
    token = await crear_instructor(db_session)

    response = await client.get(
        "/api/v1/instructor/historial",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_historial_con_evaluaciones(client: AsyncClient, db_session):
    """Test: Historial con evaluaciones."""
    token = await crear_instructor(db_session)
    aprendiz = await crear_aprendiz(db_session)
    ev = await crear_evidencia_pendiente(db_session, aprendiz.id_usuario)

    await client.put(
        f"/api/v1/instructor/evaluar/{ev.id_evidencia}",
        headers={"Authorization": f"Bearer {token}"},
        json={"estado": "Aprobada", "observaciones": "Evaluacion de prueba para historial."}
    )

    response = await client.get(
        "/api/v1/instructor/historial",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


# ====================================
# TESTS - SEGURIDAD
# ====================================

@pytest.mark.asyncio
async def test_instructor_no_autorizado(client: AsyncClient):
    """Test: Acceso sin token."""
    response = await client.get("/api/v1/instructor/perfil")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_aprendiz_no_puede_acceder_instructor(client: AsyncClient, db_session):
    """Test: Aprendiz no puede acceder a rutas de instructor."""
    from app.models.usuario import Aprendiz
    from app.services.auth_service import AuthService

    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Hack",
        correo_institucional="hack@test.com",
        numero_documento="1055555555",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="555",
        programa="ADSO"
    )
    aprendiz.establecer_contrasena("HackPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)

    token = AuthService.crear_token_acceso(
        data={"sub": aprendiz.correo_institucional, "id": aprendiz.id_usuario}
    )

    response = await client.get(
        "/api/v1/instructor/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
