# app/routes/evidencia_routes.py
"""
Rutas de evidencias: upload, listado, evaluación.
Protegidas con JWT middleware.
"""

import contextlib
import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.evidencia_schema import (
    EvaluarEvidenciaSchema,
    EvidenciaResponseSchema,
    RetroalimentacionResponseSchema,
)
from app.services.evidencia_service import EvidenciaService
from app.services.instructor_service import InstructorService

router = APIRouter(prefix="/api/v1/evidencias", tags=["Evidencias"])

# EXPLICACIÓN: Directorio donde se guardan los PDFs subidos
UPLOAD_DIR = "uploads"

# EXPLICACIÓN: Límite de tamaño de archivo (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en bytes


# ====================================
# ENDPOINTS
# ====================================

@router.post(
    "/upload",
    response_model=EvidenciaResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def upload_evidencia(
    titulo: str = Form(...),
    tipo_formato: str = Form(...),
    file: UploadFile = File(...),
    fecha_deadline: str = Form(None),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    ENDPOINT: POST /api/v1/evidencias/upload

    Sube una evidencia (PDF) al sistema.

    Args:
        titulo: Nombre de la evidencia
        tipo_formato: Tipo (Bitácora, F023, etc.)
        file: Archivo PDF a subir
        fecha_deadline: Fecha límite (opcional)
        db: Sesión de BD
        usuario: Usuario autenticado (JWT)

    Returns:
        201: Evidencia creada

    Raises:
        401: No autenticado
        403: No es aprendiz
        400: Archivo no es PDF
    """
    # Verificar que sea aprendiz
    if usuario.rol != "aprendiz":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los aprendices pueden subir evidencias"
        )

    # EXPLICACIÓN: Path(...).name descarta directorios -> neutraliza "../../x.pdf" (RNF01)
    nombre_archivo = Path(file.filename or "").name
    # EXPLICACIÓN: Rechazamos rutas vacías, sin extensión o con caracteres de traversal
    if (
        not nombre_archivo.lower().endswith(".pdf")
        or len(nombre_archivo) <= 4
        or not re.fullmatch(r"[\w\-. ]+", nombre_archivo)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo inválido: solo se permiten PDF"
        )

    # EXPLICACIÓN: Validar tamaño máximo del archivo
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )
    await file.seek(0)  # Reiniciar puntero después de leer

    # Crear directorio del aprendiz si no existe
    user_dir = Path(UPLOAD_DIR) / str(usuario.id_usuario)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Guardar archivo (usamos siempre el nombre sanitizado, nunca el del cliente)
    file_path = user_dir / nombre_archivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parsear fecha_deadline
    from datetime import datetime
    deadline = None
    if fecha_deadline:
        with contextlib.suppress(ValueError):
            deadline = datetime.fromisoformat(fecha_deadline)

    # Crear evidencia en BD
    return await EvidenciaService.crear_evidencia(
        db=db,
        id_aprendiz=usuario.id_usuario,
        titulo=titulo,
        tipo_formato=tipo_formato,
        # EXPLICACIÓN: str() porque la columna String no serializa objetos Path
        ruta_archivo=str(file_path),
        fecha_deadline=deadline
    )



@router.get(
    "/mis-evidencias",
    response_model=list[EvidenciaResponseSchema]
)
async def mis_evidencias(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    ENDPOINT: GET /api/v1/evidencias/mis-evidencias

    Lista las evidencias del aprendiz autenticado.

    Returns:
        200: Lista de evidencias
    """
    if usuario.rol != "aprendiz":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los aprendices pueden ver sus evidencias"
        )

    return await EvidenciaService.obtener_evidencias_aprendiz(
        db, usuario.id_usuario
    )


@router.get(
    "/{id_evidencia}",
    response_model=EvidenciaResponseSchema
)
async def evidencia_detail(
    id_evidencia: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    ENDPOINT: GET /api/v1/evidencias/{id_evidencia}

    Detalle de una evidencia específica.

    Args:
        id_evidencia: ID de la evidencia
    """
    evidencia = await EvidenciaService.obtener_evidencia_por_id(db, id_evidencia)
    # EXPLICACIÓN: Misma regla que descarga: sin propiedad/rol no hay metadatos (RNF01)
    EvidenciaService.verificar_acceso(usuario, evidencia)
    return evidencia


@router.put(
    "/{id_evidencia}/evaluar",
    response_model=RetroalimentacionResponseSchema
)
async def evaluar_evidencia(
    id_evidencia: int,
    datos: EvaluarEvidenciaSchema,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    ENDPOINT: PUT /api/v1/evidencias/{id_evidencia}/evaluar

    Evalúa una evidencia (solo instructores).

    Args:
        id_evidencia: ID de la evidencia
        datos: Estado + observaciones
        usuario: Instructor autenticado
    """
    if usuario.rol != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los instructores pueden evaluar evidencias"
        )

    return await InstructorService.evaluar_evidencia(
        db=db,
        id_evidencia=id_evidencia,
        id_instructor=usuario.id_usuario,
        estado=datos.estado,
        observaciones=datos.observaciones
    )



@router.get(
    "/{id_evidencia}/retroalimentacion",
    response_model=RetroalimentacionResponseSchema
)
async def retroalimentacion_detail(
    id_evidencia: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    ENDPOINT: GET /api/v1/evidencias/{id}/retroalimentacion

    Obtiene la retroalimentación de una evidencia.
    """
    retro = await EvidenciaService.obtener_retroalimentacion(db, id_evidencia)
    if not retro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esta evidencia aún no tiene retroalimentación"
        )
    return retro


@router.get("/{id_evidencia}/descarga")
async def descargar_evidencia(
    id_evidencia: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user),
):
    """
    ENDPOINT: GET /api/v1/evidencias/{id_evidencia}/descarga

    Descarga el PDF de una evidencia con autorización (RNF01).

    Args:
        id_evidencia: ID de la evidencia
        db: Sesión de BD
        usuario: Usuario autenticado (JWT)

    Returns:
        200: Archivo PDF

    Raises:
        401: No autenticado
        403: Sin acceso a la evidencia
        404: Evidencia o archivo inexistente / ruta inválida
    """
    evidencia = await EvidenciaService.obtener_evidencia_por_id(db, id_evidencia)

    # EXPLICACIÓN: Primero autorización (rol + propiedad), después la ruta
    EvidenciaService.verificar_acceso(usuario, evidencia)

    ruta = Path(evidencia.ruta_archivo_pdf).resolve()
    uploads_root = Path(UPLOAD_DIR).resolve()

    # EXPLICACIÓN: is_relative_to bloquea traversal fuera de uploads/ (RNF01)
    if not ruta.is_relative_to(uploads_root) or not ruta.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado",
        )

    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=ruta.name,
    )
