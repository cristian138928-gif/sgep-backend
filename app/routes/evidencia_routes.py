# app/routes/evidencia_routes.py
"""
Rutas de evidencias: upload, listado, evaluación.
Protegidas con JWT middleware.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase, Aprendiz, Instructor
from app.schemas.evidencia_schema import (
    EvidenciaCreateSchema,
    EvidenciaResponseSchema,
    EvaluarEvidenciaSchema,
    RetroalimentacionResponseSchema,
)
from app.services.evidencia_service import EvidenciaService
import os
import shutil

router = APIRouter(prefix="/api/v1/evidencias", tags=["Evidencias"])

# EXPLICACIÓN: Directorio donde se guardan los PDFs subidos
UPLOAD_DIR = "uploads"


# ====================================
# ENDPOINTS
# ====================================

@router.post(
    "/upload",
    response_model=EvidenciaResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def upload_evidencia(
    titulo: str,
    tipo_formato: str,
    file: UploadFile = File(...),
    fecha_deadline: str = None,
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

    # Validar que sea PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF"
        )

    # Crear directorio del aprendiz si no existe
    user_dir = os.path.join(UPLOAD_DIR, str(usuario.id_usuario))
    os.makedirs(user_dir, exist_ok=True)

    # Guardar archivo
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parsear fecha_deadline
    from datetime import datetime
    deadline = None
    if fecha_deadline:
        try:
            deadline = datetime.fromisoformat(fecha_deadline)
        except ValueError:
            pass

    # Crear evidencia en BD
    evidencia = await EvidenciaService.crear_evidencia(
        db=db,
        id_aprendiz=usuario.id_usuario,
        titulo=titulo,
        tipo_formato=tipo_formato,
        ruta_archivo=file_path,
        fecha_deadline=deadline
    )

    return evidencia


@router.get(
    "/mis-evidencias",
    response_model=List[EvidenciaResponseSchema]
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

    evidencias = await EvidenciaService.obtener_evidencias_aprendiz(
        db, usuario.id_usuario
    )
    return evidencias


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

    retro = await EvidenciaService.evaluar_evidencia(
        db=db,
        id_evidencia=id_evidencia,
        id_instructor=usuario.id_usuario,
        estado=datos.estado,
        observaciones=datos.observaciones
    )

    return retro


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
