# tests/test_reportes.py
"""
Tests de reportes CSV de coordinación (etapa B1 / RF07).
Cubre: consolidado de avance, quoting de comas, RBAC.
"""

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Coordinador, Evidencia
from app.services.auth_service import AuthService


async def _crear_coordinador(db) -> Coordinador:
    coordinador = Coordinador(
        nombre_completo="Coordinador Reportes",
        correo_institucional="coord.reportes@test.com",
        numero_documento="1044400333",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion Academica",
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db.add(coordinador)
    await db.commit()
    await db.refresh(coordinador)
    return coordinador


async def _crear_aprendiz(db, nombre: str) -> Aprendiz:
    aprendiz = Aprendiz(
        nombre_completo=nombre,
        correo_institucional="aprendiz.reporte@test.com",
        numero_documento="1044400444",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="8888888",
        programa="ADSO",
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db.add(aprendiz)
    await db.commit()
    await db.refresh(aprendiz)
    return aprendiz


async def _crear_evidencia(db, id_aprendiz: int, estado: str) -> Evidencia:
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo="Bitacora Reporte",
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test/reporte.pdf",
        estado=estado,
    )
    db.add(evidencia)
    await db.commit()
    await db.refresh(evidencia)
    return evidencia


def _token(usuario) -> str:
    return AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )


@pytest.mark.asyncio
async def test_exportar_avance_csv(client: AsyncClient, db_session):
    """RF07: consolidado de expedientes con datos y porcentajes del aprendiz."""
    coordinador = await _crear_coordinador(db_session)
    # EXPLICACIÓN: Nombre con coma => valida el quoting del csv module
    aprendiz = await _crear_aprendiz(db_session, "Perez, Juan")
    await _crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")
    await _crear_evidencia(db_session, aprendiz.id_usuario, estado="Pendiente")

    response = await client.get(
        "/api/v1/coordinador/exportar-avance",
        headers={"Authorization": f"Bearer {_token(coordinador)}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "avance_aprendices_sgep.csv" in response.headers["content-disposition"]

    contenido = response.text
    assert "id_usuario,nombre_completo,numero_ficha" in contenido
    assert '"Perez, Juan"' in contenido  # quoting correcto
    assert "8888888" in contenido
    # 1 aprobada de 2 => 50.0
    assert ",2,1,50.0" in contenido


@pytest.mark.asyncio
async def test_exportar_avance_prohibido_para_aprendiz(client: AsyncClient, db_session):
    "El reporte es exclusivo del coordinador (403)."
    aprendiz = await _crear_aprendiz(db_session, "Aprendiz Sin Rol")

    response = await client.get(
        "/api/v1/coordinador/exportar-avance",
        headers={"Authorization": f"Bearer {_token(aprendiz)}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_exportar_avance_sin_auth_401(client: AsyncClient):
    """Sin token no hay reporte (401)."""
    response = await client.get("/api/v1/coordinador/exportar-avance")
    assert response.status_code == 401
