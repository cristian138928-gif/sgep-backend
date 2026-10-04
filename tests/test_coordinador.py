# tests/test_coordinador.py
"""
Tests para endpoints del coordinador.
Cubre: estadisticas, paginacion, filtros, avance, exportar.
"""

import pytest
from httpx import AsyncClient

# ====================================
# HELPERS
# ====================================

async def crear_coordinador(db_session):
    """Crea un coordinador directamente en BD para tests."""
    from app.models.usuario import Coordinador
    from app.services.auth_service import AuthService

    coordinador = Coordinador(
        nombre_completo="Coordinador Test",
        correo_institucional="coordinador@test.com",
        numero_documento="1099999999",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion Academica"
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db_session.add(coordinador)
    await db_session.commit()
    await db_session.refresh(coordinador)

    return AuthService.crear_token_acceso(
        data={"sub": coordinador.correo_institucional, "id": coordinador.id_usuario}
    )


async def crear_aprendiz(db_session, email="aprendiz1@test.com", ficha="1111111"):
    """Crea un aprendiz en BD."""
    from app.models.usuario import Aprendiz

    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Test",
        correo_institucional=email,
        numero_documento="10" + str(hash(email))[:8],
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha=ficha,
        programa="ADSO"
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def crear_evidencia(db_session, id_aprendiz, titulo="Test", estado="Pendiente"):
    """Crea una evidencia en BD."""
    from app.models.usuario import Evidencia

    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo=titulo,
        tipo_formato="Bitacora",
        ruta_archivo_pdf="/test/test.pdf",
        estado=estado
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia


# ====================================
# TESTS - ESTADISTICAS
# ====================================

@pytest.mark.asyncio
async def test_estadisticas_vacias(client: AsyncClient, db_session):
    """Test: Estadisticas con BD vacia."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evidencias"] == 0
    assert data["aprobadas"] == 0
    assert data["total_aprendices"] == 0
    assert data["porcentaje_aprobacion"] == 0.0


@pytest.mark.asyncio
async def test_estadisticas_con_datos(client: AsyncClient, db_session):
    """Test: Estadisticas con datos en BD."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")
    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Pendiente")

    response = await client.get(
        "/api/v1/coordinador/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_evidencias"] == 2
    assert data["aprobadas"] == 1
    assert data["pendientes"] == 1
    assert data["porcentaje_aprobacion"] == 50.0


# ====================================
# TESTS - PAGINACION
# ====================================

@pytest.mark.asyncio
async def test_evidencias_paginacion(client: AsyncClient, db_session):
    """Test: Paginacion de evidencias."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    # Crear 5 evidencias
    for i in range(5):
        await crear_evidencia(db_session, aprendiz.id_usuario, titulo=f"Evidencia {i}")

    # Pagina 1, tamano 2
    response = await client.get(
        "/api/v1/coordinador/evidencias?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_evidencias_pagina_2(client: AsyncClient, db_session):
    """Test: Pagina 2 de evidencias."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    for i in range(5):
        await crear_evidencia(db_session, aprendiz.id_usuario, titulo=f"Evidencia {i}")

    response = await client.get(
        "/api/v1/coordinador/evidencias?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2


# ====================================
# TESTS - FILTROS
# ====================================

@pytest.mark.asyncio
async def test_filtro_por_estado(client: AsyncClient, db_session):
    """Test: Filtrar evidencias por estado."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")
    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Pendiente")
    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")

    response = await client.get(
        "/api/v1/coordinador/evidencias?estado=Aprobada",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["estado"] == "Aprobada"


@pytest.mark.asyncio
async def test_filtro_por_aprendiz(client: AsyncClient, db_session):
    """Test: Filtrar evidencias por aprendiz."""
    token = await crear_coordinador(db_session)
    aprendiz1 = await crear_aprendiz(db_session, email="a1@test.com", ficha="111")
    aprendiz2 = await crear_aprendiz(db_session, email="a2@test.com", ficha="222")

    await crear_evidencia(db_session, aprendiz1.id_usuario, titulo="Ev1")
    await crear_evidencia(db_session, aprendiz2.id_usuario, titulo="Ev2")

    response = await client.get(
        f"/api/v1/coordinador/evidencias?id_aprendiz={aprendiz1.id_usuario}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["titulo"] == "Ev1"


@pytest.mark.asyncio
async def test_filtro_por_tipo_formato(client: AsyncClient, db_session):
    """Test: Filtrar por tipo de formato."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    from app.models.usuario import Evidencia
    ev1 = Evidencia(
        id_aprendiz=aprendiz.id_usuario, titulo="Bitacora",
        tipo_formato="Bitacora", ruta_archivo_pdf="/test.pdf", estado="Pendiente"
    )
    ev2 = Evidencia(
        id_aprendiz=aprendiz.id_usuario, titulo="F023",
        tipo_formato="F023", ruta_archivo_pdf="/test2.pdf", estado="Pendiente"
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    response = await client.get(
        "/api/v1/coordinador/evidencias?tipo_formato=Bitacora",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["tipo_formato"] == "Bitacora"


# ====================================
# TESTS - AVANCE APRENDICES
# ====================================

@pytest.mark.asyncio
async def test_listar_aprendices_vacios(client: AsyncClient, db_session):
    """Test: Listar aprendices sin datos."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/aprendices",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_avance_aprendiz(client: AsyncClient, db_session):
    """Test: Avance de aprendiz con evidencias."""
    token = await crear_coordinador(db_session)
    aprendiz = await crear_aprendiz(db_session)

    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")
    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Aprobada")
    await crear_evidencia(db_session, aprendiz.id_usuario, estado="Pendiente")

    response = await client.get(
        "/api/v1/coordinador/aprendices",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["total_evidencias"] == 3
    assert data[0]["aprobadas"] == 2
    assert data[0]["porcentaje_avance"] == 66.67


@pytest.mark.asyncio
async def test_filtro_por_programa(client: AsyncClient, db_session):
    """Test: Filtrar aprendices por programa."""
    token = await crear_coordinador(db_session)

    from app.models.usuario import Aprendiz
    ap1 = Aprendiz(
        nombre_completo="ADSO User", correo_institucional="adso@test.com",
        numero_documento="1011111111", tipo_documento="CC", rol="aprendiz",
        numero_ficha="111", programa="ADSO"
    )
    ap1.establecer_contrasena("Pass123!")
    ap2 = Aprendiz(
        nombre_completo="Mecatronica User", correo_institucional="mec@test.com",
        numero_documento="1022222222", tipo_documento="CC", rol="aprendiz",
        numero_ficha="222", programa="Mecatronica"
    )
    ap2.establecer_contrasena("Pass123!")
    db_session.add_all([ap1, ap2])
    await db_session.commit()

    response = await client.get(
        "/api/v1/coordinador/aprendices?programa=ADSO",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["programa"] == "ADSO"


# ====================================
# TESTS - EXPORTAR CSV
# ====================================

@pytest.mark.asyncio
async def test_exportar_csv(client: AsyncClient, db_session):
    """Test: Exportar evidencias como CSV."""
    token = await crear_coordinador(db_session)

    response = await client.get(
        "/api/v1/coordinador/exportar-evidencias",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    # Verificar que tiene header CSV
    content = response.text
    assert "id,titulo,tipo_formato" in content


# ====================================
# TESTS - SEGURIDAD
# ====================================

@pytest.mark.asyncio
async def test_coordinador_no_autorizado(client: AsyncClient):
    """Test: Acceso sin token -> 401 (no autenticado, RFC 6750)."""
    response = await client.get("/api/v1/coordinador/estadisticas")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_aprendiz_no_puede_acceder_coordinador(client: AsyncClient, db_session):
    """Test: Un aprendiz no puede acceder al dashboard del coordinador."""
    from app.models.usuario import Aprendiz
    from app.services.auth_service import AuthService

    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Hack",
        correo_institucional="hack@test.com",
        numero_documento="1033333333",
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="333",
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
        "/api/v1/coordinador/estadisticas",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
