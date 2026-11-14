# tests/test_evidencias.py
"""
Tests para endpoints de evidencias.
Cubre: upload, listado, evaluación.
"""

import pytest
from httpx import AsyncClient

# ====================================
# HELPERS
# ====================================

async def registrar_y_obtener_token(client: AsyncClient) -> str:
    """Registra un aprendiz y retorna su token JWT."""
    response = await client.post(
        "/api/v1/auth/registro",
        json={
            "nombre_completo": "Luis Martínez",
            "correo_institucional": "luis@test.com",
            "contraseña": "TestPass123!",
            "numero_documento": "1088888888",
            "numero_ficha": "6666666",
            "programa": "ADSO"
        }
    )
    return response.json()["access_token"]


# ====================================
# TESTS DE EVIDENCIAS
# ====================================

@pytest.mark.asyncio
async def test_upload_evidencia(client: AsyncClient):
    """Test: POST /api/v1/evidencias/upload"""
    token = await registrar_y_obtener_token(client)

    # Crear un PDF falso para upload
    pdf_content = b"%PDF-1.4 fake content"
    response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "titulo": "Bitácora Semana 1",
            "tipo_formato": "Bitácora"
        },
        files={"file": ("bitacora.pdf", pdf_content, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Bitácora Semana 1"
    assert data["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_mis_evidencias(client: AsyncClient):
    """Test: GET /api/v1/evidencias/mis-evidencias"""
    token = await registrar_y_obtener_token(client)

    # Subir una evidencia primero
    pdf_content = b"%PDF-1.4 fake content"
    await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "titulo": "Bitácora Test",
            "tipo_formato": "Bitácora"
        },
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    # Listar evidencias
    response = await client.get(
        "/api/v1/evidencias/mis-evidencias",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_evidencia_detalle(client: AsyncClient):
    """Test: GET /api/v1/evidencias/{id}"""
    token = await registrar_y_obtener_token(client)

    # Subir evidencia
    pdf_content = b"%PDF-1.4 fake content"
    upload_response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "titulo": "Detalle Test",
            "tipo_formato": "F023"
        },
        files={"file": ("detalle.pdf", pdf_content, "application/pdf")}
    )
    evidencia_id = upload_response.json()["id_evidencia"]

    # Obtener detalle
    response = await client.get(
        f"/api/v1/evidencias/{evidencia_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["titulo"] == "Detalle Test"


@pytest.mark.asyncio
async def test_evidencia_no_encontrada(client: AsyncClient):
    """Test: GET /api/v1/evidencias/99999 (no existe)"""
    token = await registrar_y_obtener_token(client)

    response = await client.get(
        "/api/v1/evidencias/99999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


# ====================================
# TESTS DE SEGURIDAD DEL UPLOAD (RNF01/RNF02)
# ====================================

async def token_de_instructor(client: AsyncClient) -> str:
    """Registra un instructor y retorna su token JWT."""
    response = await client.post(
        "/api/v1/auth/registro-instructor",
        json={
            "nombre_completo": "Rocio Vargas",
            "correo_institucional": "rocio@test.com",
            "contraseña": "InstrPass123!",
            "numero_documento": "1099999999",
            "centro_formacion": "Centro de Salud",
            "especialidad": "Software",
        },
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_no_aprendiz_403(client: AsyncClient):
    """Test: un instructor NO sube evidencias (RBAC estricto)."""
    token = await token_de_instructor(client)

    response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"titulo": "Intento", "tipo_formato": "Bitácora"},
        files={"file": ("bitacora.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_archivo_grande_413(client: AsyncClient):
    """Test: PDF por encima de 10 MB -> 413 (no se siquiera se escribe en disco)."""
    token = await registrar_y_obtener_token(client)
    pesado = b"A" * (10 * 1024 * 1024 + 1)

    response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"titulo": "Gigante", "tipo_formato": "Bitácora"},
        files={"file": ("gigante.pdf", pesado, "application/pdf")},
    )

    assert response.status_code == 413
    assert "MB" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_deadline_iso_sin_tz(client: AsyncClient):
    """Test: fecha_deadline sin hora se asume UTC (columna timestamptz)."""
    token = await registrar_y_obtener_token(client)

    response = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "titulo": "Con deadline",
            "tipo_formato": "F028",
            "fecha_deadline": "2027-03-01",
        },
        files={"file": ("f028.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["fecha_deadline"].startswith("2027-03-01")


@pytest.mark.asyncio
async def test_mis_evidencias_no_aprendiz_403(client: AsyncClient):
    """Test: un instructor no lista "mis evidencias" de aprendiz."""
    token = await token_de_instructor(client)

    response = await client.get(
        "/api/v1/evidencias/mis-evidencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_retroalimentacion_inexistente_404(client: AsyncClient):
    """Test: evidencia sin evaluar -> 404 al pedir su retroalimentación."""
    token = await registrar_y_obtener_token(client)

    upload = await client.post(
        "/api/v1/evidencias/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"titulo": "Sin evaluar", "tipo_formato": "Bitácora"},
        files={"file": ("sin_evaluar.pdf", b"%PDF-1.4", "application/pdf")},
    )
    evidencia_id = upload.json()["id_evidencia"]

    response = await client.get(
        f"/api/v1/evidencias/{evidencia_id}/retroalimentacion",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "no tiene retroalimentación" in response.json()["detail"]
