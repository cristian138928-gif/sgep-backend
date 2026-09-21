# app/routes/instructor_routes.py
"""
Rutas del dashboard de instructor.
Evaluacion de evidencias, historial, estadisticas personales.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.evidencia_schema import EvidenciaResponseSchema
from app.schemas.instructor_schema import (
    EstadisticasInstructorSchema,
    InstructorPerfilSchema,
    EvaluarEvidenciaSchema,
    RetroalimentacionResponseSchema,
)
from app.schemas.coordinador_schema import PaginacionSchema
from app.services.instructor_service import InstructorService

router = APIRouter(prefix="/api/v1/instructor", tags=["Instructor"])


# ====================================
# MIDDLEWARE: Verificar rol instructor
# ====================================

async def verificar_instructor(
    usuario: UsuarioBase = Depends(get_current_user)
) -> UsuarioBase:
    """Dependencia que verifica que el usuario sea instructor."""
    if usuario.rol != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los instructores pueden acceder a este recurso"
        )
    return usuario


# ====================================
# ENDPOINTS
# ====================================

@router.get("/perfil", response_model=InstructorPerfilSchema)
async def mi_perfil(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    ENDPOINT: GET /api/v1/instructor/perfil
    
    Obtiene el perfil del instructor autenticado.
    """
    from sqlalchemy import select
    from app.models.usuario import Instructor

    stmt = select(Instructor).where(Instructor.id_usuario == usuario.id_usuario)
    resultado = await db.execute(stmt)
    instructor = resultado.scalars().first()

    return {
        "id_usuario": instructor.id_usuario,
        "nombre_completo": instructor.nombre_completo,
        "correo_institucional": instructor.correo_institucional,
        "centro_formacion": instructor.centro_formacion,
        "especialidad": instructor.especialidad
    }


@router.get("/estadisticas", response_model=EstadisticasInstructorSchema)
async def estadisticas(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    ENDPOINT: GET /api/v1/instructor/estadisticas
    
    Estadisticas personales del instructor.
    Incluye: total evaluadas, aprobadas, ajustes, pendientes.
    """
    stats = await InstructorService.obtener_estadisticas(db, usuario.id_usuario)
    return stats


@router.get(
    "/evidencias-pendientes",
    response_model=PaginacionSchema[EvidenciaResponseSchema]
)
async def evidencias_pendientes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    ENDPOINT: GET /api/v1/instructor/evidencias-pendientes
    
    Lista evidencias pendientes de evaluacion (paginadas).
    """
    resultado = await InstructorService.obtener_evidencias_pendientes(
        db, page=page, page_size=page_size
    )
    return resultado


@router.put(
    "/evaluar/{id_evidencia}",
    response_model=RetroalimentacionResponseSchema
)
async def evaluar(
    id_evidencia: int,
    datos: EvaluarEvidenciaSchema,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    ENDPOINT: PUT /api/v1/instructor/evaluar/{id_evidencia}
    
    Evalua una evidencia y crea retroalimentacion.
    
    Estados validos:
    - "Aprobada": Evidencia cumple requisitos
    - "Ajuste Requerido": Necesita correcciones
    """
    retro = await InstructorService.evaluar_evidencia(
        db=db,
        id_evidencia=id_evidencia,
        id_instructor=usuario.id_usuario,
        estado=datos.estado,
        observaciones=datos.observaciones
    )
    return retro


@router.get(
    "/historial",
    response_model=PaginacionSchema[RetroalimentacionResponseSchema]
)
async def historial(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor)
):
    """
    ENDPOINT: GET /api/v1/instructor/historial
    
    Historial de evaluaciones del instructor (paginado).
    """
    resultado = await InstructorService.obtener_historial_evaluaciones(
        db, usuario.id_usuario, page=page, page_size=page_size
    )
    return resultado
