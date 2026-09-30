# tests/test_alertas.py
"""
Tests del endpoint GET /api/v1/aprendiz/alertas.
Cubre: vencidas, por vencer, ventana de días, estados y RBAC.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Coordinador, Evidencia
from app.services.auth_service import AuthService


# ====================================
# HELPERS
# ====================================

async def crear_aprendiz_bd(db_session) -> Aprendiz:
    """Crea un aprendiz en BD y retorna su JWT junto con él."""
    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Alertas",
        correo_institucional="alertas@test.com",
        numero_documento="1055555555",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="8888888",
        programa="ADSO",
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def token_de(usuario) -> str:
    """Genera JWT para un usuario ya persistido."""
    return AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )


async def crear_evidencia_bd(
    db_session,
    id_aprendiz: int,
    dias_limite: int,
    estado: str = "Pendiente",
    titulo: str = "Bitacora",
) -> Evidencia:
    """Crea una evidencia con deadline relativo a hoy (positivo o negativo)."""
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo=titulo,
        tipo_formato="Bitacora",
        ruta_archivo_pdf="uploads/alerta.pdf",
        estado=estado,
        fecha_deadline=datetime.now(timezone.utc) + timedelta(days=dias_limite),
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia


# ====================================
# TESTS DE CLASIFICACIÓN
# ====================================

@pytest.mark.asyncio
async def test_alertas_lista_vacia(client: AsyncClient, db_session):
    """200: aprendiz sin evidencias => lista vacía."""
    aprendiz = await crear_aprendiz_bd(db_session)
    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_alerta_vencida(client: AsyncClient, db_session):
    """Deadline en el pasado => 'Vencida' con dias_restantes negativos."""
    aprendiz = await crear_aprendiz_bd(db_session)
    evidencia = await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=-2)

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    alertas = response.json()
    assert len(alertas) == 1
    assert alertas[0]["id_evidencia"] == evidencia.id_evidencia
    assert alertas[0]["estado_alerta"] == "Vencida"
    assert alertas[0]["dias_restantes"] < 0


@pytest.mark.asyncio
async def test_alerta_por_vencer(client: AsyncClient, db_session):
    """Deadline dentro de la ventana por defecto (7 días) => 'Por vencer'."""
    aprendiz = await crear_aprendiz_bd(db_session)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=3)

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    alertas = response.json()
    assert len(alertas) == 1
    assert alertas[0]["estado_alerta"] == "Por vencer"
    assert 0 <= alertas[0]["dias_restantes"] <= 7


@pytest.mark.asyncio
async def test_alerta_fuera_de_ventana_no_aparece(client: AsyncClient, db_session):
    """Deadline a 30 días con ventana de 7 => sin alerta."""
    aprendiz = await crear_aprendiz_bd(db_session)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=30)

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.json() == []


@pytest.mark.asyncio
async def test_alerta_ventana_ampliada(client: AsyncClient, db_session):
    """?dias=30 hace visible el deadline de 30 días."""
    aprendiz = await crear_aprendiz_bd(db_session)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=30)

    response = await client.get(
        "/api/v1/aprendiz/alertas?dias=30",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_alerta_ignora_aprobadas(client: AsyncClient, db_session):
    """Evidencia Aprobada con deadline vencido => no genera alerta."""
    aprendiz = await crear_aprendiz_bd(db_session)
    await crear_evidencia_bd(
        db_session, aprendiz.id_usuario, dias_limite=-5, estado="Aprobada"
    )

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.json() == []


@pytest.mark.asyncio
async def test_alertas_ordenadas_por_urgencia(client: AsyncClient, db_session):
    """Las vencidas (días negativos) van primero."""
    aprendiz = await crear_aprendiz_bd(db_session)
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=2, titulo="Cerca")
    await crear_evidencia_bd(db_session, aprendiz.id_usuario, dias_limite=-1, titulo="Vencida")

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    alertas = response.json()
    assert len(alertas) == 2
    assert alertas[0]["estado_alerta"] == "Vencida"
    assert alertas[1]["estado_alerta"] == "Por vencer"


# ====================================
# TESTS DE RBAC Y VALIDACIÓN
# ====================================

@pytest.mark.asyncio
async def test_alertas_no_aprendiz_403(client: AsyncClient, db_session):
    """403: coordinador no puede consultar /aprendiz/alertas."""
    coordinador = Coordinador(
        nombre_completo="Coord Alertas",
        correo_institucional="coord_alertas@test.com",
        numero_documento="1044444444",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion",
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db_session.add(coordinador)
    await db_session.commit()

    response = await client.get(
        "/api/v1/aprendiz/alertas",
        headers={"Authorization": f"Bearer {await token_de(coordinador)}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_alertas_dias_fuera_de_rango_422(client: AsyncClient, db_session):
    """422: ?dias=100 excede el límite permitido (le=90)."""
    aprendiz = await crear_aprendiz_bd(db_session)

    response = await client.get(
        "/api/v1/aprendiz/alertas?dias=100",
        headers={"Authorization": f"Bearer {await token_de(aprendiz)}"},
    )

    assert response.status_code == 422
