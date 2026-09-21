# app/routes/coordinador_routes.py
"""
Rutas del dashboard de coordinador.
Supervision de evidencias, estadisticas, avance de aprendices.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.evidencia_schema import EvidenciaResponseSchema
from app.schemas.coordinador_schema import (
    EstadisticasSchema,
    AvanceAprendizSchema,
    InstructorResponseSchema,
    PaginacionSchema,
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
    
    Estadisticas generales del sistema.
    Incluye: total evidencias, aprobadas, pendientes, ajustes,
             total aprendices, instructores, porcentaje aprobacion.
    """
    stats = await CoordinadorService.obtener_estadisticas(db)
    return stats


@router.get("/evidencias", response_model=PaginacionSchema[EvidenciaResponseSchema])
async def listar_evidencias(
    page: int = Query(1, ge=1, description="Numero de pagina"),
    page_size: int = Query(10, ge=1, le=50, description="Elementos por pagina"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    id_aprendiz: Optional[int] = Query(None, description="Filtrar por aprendiz"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha inicio (ISO)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha fin (ISO)"),
    tipo_formato: Optional[str] = Query(None, description="Tipo de formato"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/evidencias
    
    Lista paginada de evidencias con filtros avanzados.
    
    Filtros:
        - estado: "Pendiente", "Aprobada", "Ajuste Requerido"
        - id_aprendiz: ID del aprendiz
        - fecha_desde / fecha_hasta: Rango de fechas (ISO format)
        - tipo_formato: "Bitacora", "F023", etc.
    
    Paginacion:
        - page: Numero de pagina (default 1)
        - page_size: Elementos por pagina (1-50, default 10)
    """
    resultado = await CoordinadorService.obtener_evidencias_paginadas(
        db,
        page=page,
        page_size=page_size,
        estado=estado,
        id_aprendiz=id_aprendiz,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_formato=tipo_formato
    )
    return resultado


@router.get("/aprendices", response_model=List[AvanceAprendizSchema])
async def listar_aprendices_con_avance(
    programa: Optional[str] = Query(None, description="Filtrar por programa"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/aprendices
    
    Lista aprendices con su porcentaje de avance.
    Filtro opcional por programa.
    """
    avances = await CoordinadorService.obtener_avance_aprendices(db, programa=programa)
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


@router.get("/exportar-evidencias")
async def exportar_evidencias(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/exportar-evidencias
    
    Exporta todas las evidencias como archivo CSV.
    Descarga automatica en el navegador.
    """
    csv_content = await CoordinadorService.exportar_evidencias_csv(db)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=evidencias_sgep.csv"
        }
    )
