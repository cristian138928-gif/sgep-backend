# app/routes/instructor_routes.py
"""
Rutas del dashboard de instructor.
Evaluacion de evidencias, historial, estadisticas personales.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.coordinador_schema import PaginacionSchema
from app.schemas.evidencia_schema import (
    AlertaVencimientoRolSchema,
    EvaluarEvidenciaSchema,
    EvidenciaResponseSchema,
    RetroalimentacionResponseSchema,
)
from app.schemas.instructor_schema import (
    EstadisticasInstructorSchema,
    InstructorPerfilSchema,
)
from app.services.asignacion_service import AsignacionService
from app.services.evidencia_service import EvidenciaService
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
    instructor = await InstructorService.obtener_perfil(db, usuario.id_usuario)

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
    return await InstructorService.obtener_estadisticas(db, usuario.id_usuario)


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
    return await InstructorService.obtener_evidencias_pendientes(
        db, page=page, page_size=page_size
    )


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
    return await InstructorService.evaluar_evidencia(
        db=db,
        id_evidencia=id_evidencia,
        id_instructor=usuario.id_usuario,
        estado=datos.estado,
        observaciones=datos.observaciones
    )


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
    return await InstructorService.obtener_historial_evaluaciones(
        db, usuario.id_usuario, page=page, page_size=page_size
    )


@router.get("/alertas", response_model=list[AlertaVencimientoRolSchema])
async def mis_alertas(
    dias: int = Query(7, ge=0, le=90, description="Dias de anticipacion"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_instructor),
):
    """
    ENDPOINT: GET /api/v1/instructor/alertas?dias=7

    Vencimientos de las evidencias pendientes de los aprendices
    asignados activamente a este instructor.

    Args:
        dias: Ventana de anticipacion (0-90), por defecto 7
        db: Sesion de BD
        usuario: Instructor autenticado (JWT)

    Returns:
        200: Alertas con nombre_aprendiz ordenadas por urgencia
        403: Si el rol no es instructor
    """
    asignaciones = await AsignacionService.listar_aprendices_instructor(
        db, usuario.id_usuario
    )
    return await EvidenciaService.obtener_alertas_rol(
        db=db,
        ids_aprendiz=[a["id_aprendiz"] for a in asignaciones],
        dias_anticipacion=dias,
    )
