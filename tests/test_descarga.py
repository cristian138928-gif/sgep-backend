# tests/test_descarga.py
"""
Tests de descarga segura de PDFs (RNF01).
Cubre: autorización por rol, propiedad, traversal de ruta y sanitización de upload.
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.models.usuario import Aprendiz, Coordinador, Evidencia, Instructor
from app.services.auth_service import AuthService

# ====================================
# HELPERS
# ====================================

async def crear_aprendiz_bd(db_session, email: str) -> Aprendiz:
    """Crea un aprendiz directamente en BD (patrón del resto de la suite)."""
    aprendiz = Aprendiz(
        nombre_completo="Aprendiz Descarga",
        correo_institucional=email,
        numero_documento="10" + str(abs(hash(email)))[:8],
        tipo_documento="CC",
        rol="aprendiz",
        numero_ficha="7777777",
        programa="ADSO",
    )
    aprendiz.establecer_contrasena("AprendizPass123!")
    db_session.add(aprendiz)
    await db_session.commit()
    await db_session.refresh(aprendiz)
    return aprendiz


async def crear_instructor_bd(db_session, email: str = "inst_desc@test.com") -> Instructor:
    """Crea un instructor directamente en BD."""
    instructor = Instructor(
        nombre_completo="Instructor Descarga",
        correo_institucional=email,
        numero_documento="10" + str(abs(hash(email)))[:8],
        tipo_documento="CC",
        rol="instructor",
        centro_formacion="Centro Salud",
        especialidad="Software",
    )
    instructor.establecer_contrasena("InstructorPass123!")
    db_session.add(instructor)
    await db_session.commit()
    await db_session.refresh(instructor)
    return instructor


async def token_de(usuario) -> str:
    """Genera el JWT para un usuario ya creado en BD."""
    return AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )


async def crear_coordinador_bd(db_session) -> Coordinador:
    """Crea un coordinador directamente en BD."""
    coordinador = Coordinador(
        nombre_completo="Coordinador Descarga",
        correo_institucional="coord_desc@test.com",
        numero_documento="1098765432",
        tipo_documento="CC",
        rol="coordinador",
        departamento="Coordinacion Academica",
    )
    coordinador.establecer_contrasena("CoordPass123!")
    db_session.add(coordinador)
    await db_session.commit()
    await db_session.refresh(coordinador)
    return coordinador


async def crear_evidencia_bd(
    db_session, id_aprendiz: int, ruta: str = "uploads/test.pdf"
) -> Evidencia:
    """Crea una evidencia en BD con ruta controlada por el test."""
    evidencia = Evidencia(
        id_aprendiz=id_aprendiz,
        titulo="Evidencia Descarga",
        tipo_formato="Bitacora",
        ruta_archivo_pdf=ruta,
        estado="Pendiente",
    )
    db_session.add(evidencia)
    await db_session.commit()
    await db_session.refresh(evidencia)
    return evidencia


async def registrar_aprendiz(client: AsyncClient, email: str) -> str:
    """Registra un aprendiz vía API y retorna su JWT."""
    response = await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Aprendiz Descarga",
            "correo_institucional": email,
            "contraseña": "TestPass123!",
            "numero_documento": "10" + str(abs(hash(email)))[:8],
            # EXPLICACIÓN: numero_ficha es UNIQUE => derivamos uno distinto por email
            "numero_ficha": str(1000000 + abs(hash(email)) % 9000000),
            "programa": "ADSO",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def subir_pdf(client: AsyncClient, token: str, nombre: str = "bitacora.pdf"):
    """Sube un PDF de prueba y retorna la respuesta."""
    return await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"titulo": "Bitacora Descarga", "tipo_formato": "Bitacora"},
        files={"file": (nombre, b"%PDF-1.4 contenido fake", "application/pdf")},
    )


@pytest.fixture
def limpiar_uploads():
    """Borra solo los archivos creados durante el test (uploads/ es compartido)."""
    raiz = Path("uploads")
    antes = {p for p in raiz.rglob("*") if p.is_file()} if raiz.exists() else set()
    yield
    nuevos = {p for p in raiz.rglob("*") if p.is_file()} - antes
    for archivo in nuevos:
        archivo.unlink(missing_ok=True)


# ====================================
# TESTS DE AUTORIZACIÓN (RBAC + PROPIEDAD)
# ====================================

@pytest.mark.asyncio
async def test_descarga_propietario_recibe_pdf(client: AsyncClient, limpiar_uploads):
    """200: el aprendiz dueño descarga su propio PDF."""
    token = await registrar_aprendiz(client, "dueno@test.com")
    id_ev = (await subir_pdf(client, token)).json()["id_evidencia"]

    response = await client.get(
        f"/api/v1/evidencias/{id_ev}/descarga",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_descarga_otro_aprendiz_prohibido(client: AsyncClient, limpiar_uploads):
    """403: un aprendiz distinto no descarga evidencias ajenas."""
    token_dueno = await registrar_aprendiz(client, "dueno2@test.com")
    id_ev = (await subir_pdf(client, token_dueno)).json()["id_evidencia"]
    token_intruso = await registrar_aprendiz(client, "intruso@test.com")

    response = await client.get(
        f"/api/v1/evidencias/{id_ev}/descarga",
        headers={"Authorization": f"Bearer {token_intruso}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_descarga_coordinador_recibe_pdf(
    client: AsyncClient, db_session, limpiar_uploads
):
    """200: el coordinador tiene acceso total (RBAC)."""
    token_aprendiz = await registrar_aprendiz(client, "coord_case@test.com")
    id_ev = (await subir_pdf(client, token_aprendiz)).json()["id_evidencia"]
    coordinador = await crear_coordinador_bd(db_session)
    token_coord = await token_de(coordinador)

    response = await client.get(
        f"/api/v1/evidencias/{id_ev}/descarga",
        headers={"Authorization": f"Bearer {token_coord}"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_descarga_instructor_recibe_pdf(
    client: AsyncClient, db_session, limpiar_uploads
):
    """200: el instructor necesita el PDF para evaluar."""
    token_aprendiz = await registrar_aprendiz(client, "inst_case@test.com")
    id_ev = (await subir_pdf(client, token_aprendiz)).json()["id_evidencia"]
    instructor = await crear_instructor_bd(db_session)
    token_inst = await token_de(instructor)

    response = await client.get(
        f"/api/v1/evidencias/{id_ev}/descarga",
        headers={"Authorization": f"Bearer {token_inst}"},
    )

    assert response.status_code == 200


# ====================================
# TESTS DE RUTA / INTEGRIDAD
# ====================================

@pytest.mark.asyncio
async def test_descarga_inexistente_404(client: AsyncClient):
    """404: evidencia que no existe en BD."""
    token = await registrar_aprendiz(client, "noexiste@test.com")

    response = await client.get(
        "/api/v1/evidencias/99999/descarga",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_descarga_ruta_fuera_de_uploads_404(client: AsyncClient, db_session):
    """404: ruta en BD que escapa de uploads/ (defensa en profundidad)."""
    aprendiz = await crear_aprendiz_bd(db_session, email="fuga@test.com")
    evidencia = await crear_evidencia_bd(db_session, aprendiz.id_usuario)
    # EXPLICACIÓN: Ruta relativa a la raíz del proyecto => is_relative_to falla
    evidencia.ruta_archivo_pdf = "README.md"
    await db_session.commit()

    jwt = await token_de(aprendiz)

    response = await client.get(
        f"/api/v1/evidencias/{evidencia.id_evidencia}/descarga",
        headers={"Authorization": f"Bearer {jwt}"},
    )

    assert response.status_code == 404
    assert "Archivo no encontrado" in response.json()["detail"]


# ====================================
# TESTS DE SANITIZACIÓN EN UPLOAD
# ====================================

@pytest.mark.asyncio
async def test_upload_traversal_se_sanitiza(client: AsyncClient, limpiar_uploads):
    """201 + ruta limpia: '../../evil.pdf' se guarda como 'evil.pdf' dentro de uploads/."""
    token = await registrar_aprendiz(client, "traversal@test.com")

    response = await subir_pdf(client, token, nombre="../../evil.pdf")

    assert response.status_code == 201
    ruta = response.json()["ruta_archivo_pdf"]
    assert ".." not in ruta
    assert Path(ruta).resolve().is_relative_to(Path("uploads").resolve())
    assert Path(ruta).is_file()


@pytest.mark.asyncio
async def test_upload_no_pdf_rechazado(client: AsyncClient):
    """400: archivos que no son PDF no entran."""
    token = await registrar_aprendiz(client, "no_pdf@test.com")

    response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"titulo": "Nota txt", "tipo_formato": "Bitacora"},
        files={"file": ("nota.txt", b"texto plano", "text/plain")},
    )

    assert response.status_code == 400
