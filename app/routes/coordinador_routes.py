# app/routes/coordinador_routes.py
"""
Rutas del dashboard de coordinador.
Supervisión de evidencias, estadísticas, avance de aprendices.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.evidencia_schema import EvidenciaResponseSchema
from app.schemas.coordinador_schema import (
    EstadisticasSchema,
    AvanceAprendizSchema,
    InstructorResponseSchema,
)
from app.services.coordinador_service import CoordinadorService

router = APIRouter(prefix="/api/v1/coordinador", tags=["Coordinador"])


# ====================================
# MIDDLEWARE: Verificar rol coordinador
# ====================================

async def verificar_coordinador(
    usuario: UsuarioBase = Depends(get_current_user)
) -> UsuarioBase:
    """
    Dependencia que verifica que el usuario sea coordinador.
    Se reutiliza en todos los endpoints de este archivo.
    """
    if usuario.rol != "coordinador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los coordinadores pueden acceder a este recurso"
        )
    return usuario


# ====================================
# ENDPOINTS
# ====================================

@router.get("/estadisticas", response_model=EstadisticasSchema)
async def estadisticas(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/estadisticas
    
    Obtiene estadísticas generales del sistema.
    
    Returns:
        200: Estadísticas (total evidencias, aprobadas, pendientes, etc.)
    """
    stats = await CoordinadorService.obtener_estadisticas(db)
    return stats


@router.get("/evidencias", response_model=List[EvidenciaResponseSchema])
async def listar_evidencias(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    id_aprendiz: Optional[int] = Query(None, description="Filtrar por aprendiz"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/evidencias
    
    Lista todas las evidencias del sistema con filtros opcionales.
    
    Query params:
        - estado: "Pendiente", "Aprobada", "Ajuste Requerido"
        - id_aprendiz: ID del aprendiz
    """
    evidencias = await CoordinadorService.obtener_todas_evidencias(
        db, estado=estado, id_aprendiz=id_aprendiz
    )
    return evidencias


@router.get("/aprendices", response_model=List[AvanceAprendizSchema])
async def listar_aprendices_con_avance(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/aprendices
    
    Lista todos los aprendices con su porcentaje de avance.
    """
    avances = await CoordinadorService.obtener_avance_aprendices(db)
    return avances


@router.get("/instructores", response_model=List[InstructorResponseSchema])
async def listar_instructores(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/instructores
    
    Lista todos los instructores del sistema.
    """
    instructores = await CoordinadorService.obtener_instructores(db)
    return instructores
