# tests/test_notificaciones.py
"""
Tests de notificaciones in-app (etapa B2).
Cubre: creación al evaluar, listado propio, badge, dedupe de vencimientos.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Evidencia, Instructor
from app.services.auth_service import AuthService
from app.services.notificacion_service import NotificacionService

OBSERVACIONES = "Buena bitacora, cumple con los requisitos minimos."


async def _crear_aprendiz(db) -> Aprendiz:
    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Notif",
        correo_institucional="aprendiz.notif@test.com",
        numero_documento="1055500111",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="9999999",
        programa="ADSO",
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db.add(aprendiz)
    await db.commit()
    await db.refresh(aprendiz)
    return aprendiz


async def _crear_instructor(db) -> Instructor:
    instructor = Instructor(
        nombre_completo="Instructor Notif",
        correo_institucional="instructor.notif@test.com",
        numero_documento="1055500222",
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software",
    )
    instructor.establecer_contrasena("InstructorPass123!")
    db.add(instructor)
    await db.commit()
    await db.refresh(instructor)
    return instructor


def _token(usuario) -> str:
    return AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )


async def _crear_evidencia(db, id_aprendiz, deadline=None) -> Evidencia:
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo="Bitacora Notif",
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test/notif.pdf",
        estado="Pendiente",
        fecha_deadline=deadline,
    )
    db.add(evidencia)
    await db.commit()
    await db.refresh(evidencia)
    return evidencia


# ====================================
# TESTS - CREACIÓN AL EVALUAR
# ====================================

@pytest.mark.asyncio
async def test_evaluar_crea_notificacion_al_aprendiz(client: AsyncClient, db_session):
    """Evaluar una evidencia genera una notificación in-app al aprendiz."""
    aprendiz = await _crear_aprendiz(db_session)
    instructor = await _crear_instructor(db_session)
    evidencia = await _crear_evidencia(db_session, aprendiz.id_usuario)

    response = await client.put(
        f"/api/v1/instructor/evaluar/{evidencia.id_evidencia}",
        json={"estado": "Aprobada", "observaciones": OBSERVACIONES},
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )
    assert response.status_code == 200

    notifs = await client.get(
        "/api/v1/notificaciones",
        headers={"Authorization": f"Bearer {_token(aprendiz)}"},
    )

    assert notifs.status_code == 200
    items = notifs.json()
    assert len(items) == 1
    assert items[0]["tipo"] == "evaluacion"
    assert "Aprobada" in items[0]["mensaje"]
    assert items[0]["leida"] is False


@pytest.mark.asyncio
async def test_notificaciones_solo_propias(client: AsyncClient, db_session):
    """Cada usuario solo ve LAS SUYAS (no las del resto)."""
    aprendiz = await _crear_aprendiz(db_session)
    instructor = await _crear_instructor(db_session)
    evidencia = await _crear_evidencia(db_session, aprendiz.id_usuario)

    await client.put(
        f"/api/v1/instructor/evaluar/{evidencia.id_evidencia}",
        json={"estado": "Aprobada", "observaciones": OBSERVACIONES},
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )

    propias_instructor = await client.get(
        "/api/v1/notificaciones",
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )

    assert propias_instructor.status_code == 200
    assert propias_instructor.json() == []


@pytest.mark.asyncio
async def test_conteo_y_marcar_leida(client: AsyncClient, db_session):
    """El badge cuenta no leídas y marcar leída lo pone a cero."""
    aprendiz = await _crear_aprendiz(db_session)
    instructor = await _crear_instructor(db_session)
    evidencia = await _crear_evidencia(db_session, aprendiz.id_usuario)
    token_aprendiz = {"Authorization": f"Bearer {_token(aprendiz)}"}

    await client.put(
        f"/api/v1/instructor/evaluar/{evidencia.id_evidencia}",
        json={"estado": "Aprobada", "observaciones": OBSERVACIONES},
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )

    badge = await client.get("/api/v1/notificaciones/no-leidas", headers=token_aprendiz)
    assert badge.json() == {"no_leidas": 1}

    id_notif = (await client.get("/api/v1/notificaciones", headers=token_aprendiz)).json()[0][
        "id_notificacion"
    ]
    marcada = await client.post(
        f"/api/v1/notificaciones/{id_notif}/marcar-leida", headers=token_aprendiz
    )

    assert marcada.status_code == 200
    assert marcada.json()["leida"] is True
    badge_final = await client.get(
        "/api/v1/notificaciones/no-leidas", headers=token_aprendiz
    )
    assert badge_final.json() == {"no_leidas": 0}


@pytest.mark.asyncio
async def test_marcar_todas_leidas(client: AsyncClient, db_session):
    """POST marcar-todas-leidas pone el badge a cero en una sola acción."""
    aprendiz = await _crear_aprendiz(db_session)
    instructor = await _crear_instructor(db_session)
    # EXPLICACIÓN: Dos evidencias => 2 notificaciones (re-evaluar da 409)
    ev1 = await _crear_evidencia(db_session, aprendiz.id_usuario)
    ev2 = await _crear_evidencia(db_session, aprendiz.id_usuario)
    ev2.titulo = "Bitacora 2"
    await db_session.commit()
    token_aprendiz = {"Authorization": f"Bearer {_token(aprendiz)}"}

    for evidencia in (ev1, ev2):
        await client.put(
            f"/api/v1/instructor/evaluar/{evidencia.id_evidencia}",
            json={"estado": "Aprobada", "observaciones": OBSERVACIONES},
            headers={"Authorization": f"Bearer {_token(instructor)}"},
        )

    badge = await client.get("/api/v1/notificaciones/no-leidas", headers=token_aprendiz)
    assert badge.json() == {"no_leidas": 2}

    todas = await client.post(
        "/api/v1/notificaciones/marcar-todas-leidas", headers=token_aprendiz
    )

    assert todas.status_code == 200
    assert todas.json() == {"no_leidas": 0}
    lista = (await client.get("/api/v1/notificaciones", headers=token_aprendiz)).json()
    assert len(lista) == 2
    assert all(n["leida"] for n in lista)


@pytest.mark.asyncio
async def test_marcar_todas_sin_auth_401(client: AsyncClient):
    """Sin token no se puede marcar nada como leído."""
    response = await client.post("/api/v1/notificaciones/marcar-todas-leidas")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_marcar_leida_ajena_retorna_404(client: AsyncClient, db_session):
    """Marcar la notificación de otro usuario → 404 (no filtra existencia)."""
    aprendiz = await _crear_aprendiz(db_session)
    instructor = await _crear_instructor(db_session)
    evidencia = await _crear_evidencia(db_session, aprendiz.id_usuario)

    await client.put(
        f"/api/v1/instructor/evaluar/{evidencia.id_evidencia}",
        json={"estado": "Aprobada", "observaciones": OBSERVACIONES},
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )

    respuesta = await client.post(
        "/api/v1/notificaciones/1/marcar-leida",
        headers={"Authorization": f"Bearer {_token(instructor)}"},
    )

    assert respuesta.status_code == 404


@pytest.mark.asyncio
async def test_notificaciones_sin_auth_401(client: AsyncClient):
    """Sin token no se consultan notificaciones."""
    response = await client.get("/api/v1/notificaciones")
    assert response.status_code == 401


# ====================================
# TESTS - ALERTAS DE VENCIMIENTO (SERVICIO)
# ====================================

@pytest.mark.asyncio
async def test_generar_alertas_vencimiento_dedup(db_session):
    """Materializa la alerta UNA sola vez aunque se ejecute dos veces."""
    aprendiz = await _crear_aprendiz(db_session)
    manana = datetime.now(UTC) + timedelta(days=1)
    await _crear_evidencia(db_session, aprendiz.id_usuario, deadline=manana)

    primera = await NotificacionService.generar_alertas_vencimiento(db_session)
    segunda = await NotificacionService.generar_alertas_vencimiento(db_session)

    assert primera == 1
    assert segunda == 0  # EXPLICACIÓN: dedupe por evidencia + tipo no leída

    no_leidas = await NotificacionService.contar_no_leidas(
        db_session, aprendiz.id_usuario
    )
    assert no_leidas == 1


@pytest.mark.asyncio
async def test_generar_alertas_fuera_de_ventana(db_session):
    "Deadline lejano (30 días) no genera alerta con ventana de 7."
    aprendiz = await _crear_aprendiz(db_session)
    lejano = datetime.now(UTC) + timedelta(days=30)
    await _crear_evidencia(db_session, aprendiz.id_usuario, deadline=lejano)

    creadas = await NotificacionService.generar_alertas_vencimiento(
        db_session, dias_anticipacion=7
    )

    assert creadas == 0
