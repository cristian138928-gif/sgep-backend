# app/routes/retroalimentacion_routes.py
"""
Rutas de retroalimentacion independiente.
Endpoint POST /api/v1/retroalimentacion/ para crear comentarios
sin necesidad de usar el flujo de evaluacion.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.evidencia_schema import (
    RetroalimentacionCreateSchema,
    RetroalimentacionResponseSchema,
)
from app.services.evidencia_service import EvidenciaService
from app.services.retroalimentacion_service import RetroalimentacionService

router = APIRouter(prefix="/api/v1/retroalimentacion", tags=["Retroalimentacion"])


async def verificar_instructor(
    usuario: UsuarioBase = Depends(get_current_user)
) -> UsuarioBase:
    """Solo instructores crean retroalimentacion."""
    if usuario.rol != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los instructores pueden crear retroalimentacion"
        )
    return usuario


@router.post(
    "/",
    response_model=RetroalimentacionResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def crear_retroalimentacion(
    datos: RetroalimentacionCreateSchema,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    POST /api/v1/retroalimentacion/

    Crea retroalimentacion independiente para una evidencia.

    El estado_evaluacion es opcional:
    - Si se envia: actualiza el estado de la evidencia
    - Si no se envia: solo agrega comentario sin cambiar estado
    """
    return await RetroalimentacionService.crear(
        db=db,
        id_evidencia=datos.id_evidencia,
        id_instructor=usuario.id_usuario,
        observaciones=datos.observaciones,
        estado_evaluacion=datos.estado_evaluacion
    )


@router.get("/{id_retroalimentacion}", response_model=RetroalimentacionResponseSchema)
async def ver_retroalimentacion(
    id_retroalimentacion: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    GET /api/v1/retroalimentacion/{id}

    Obtiene una retroalimentacion por su ID.
    """
    retro = await RetroalimentacionService.obtener_por_id(db, id_retroalimentacion)
    # EXPLICACIÓN: sin verificar acceso, cualquier usuario leería comentarios ajenos (RNF01)
    evidencia = await EvidenciaService.obtener_evidencia_por_id(db, retro.id_evidencia)
    EvidenciaService.verificar_acceso(usuario, evidencia)
    return retro
