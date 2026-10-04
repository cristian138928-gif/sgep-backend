# app/routes/coordinador_routes.py
"""
Rutas del dashboard de coordinador.
Supervision de evidencias, estadisticas, avance de aprendices.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.coordinador_schema import (
    AvanceAprendizSchema,
    EstadisticasSchema,
    InstructorResponseSchema,
    PaginacionSchema,
)
from app.schemas.evidencia_schema import (
    AlertaVencimientoRolSchema,
    EvidenciaResponseSchema,
)
from app.services.coordinador_service import CoordinadorService
from app.services.evidencia_service import EvidenciaService

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
    return await CoordinadorService.obtener_estadisticas(db)


@router.get("/evidencias", response_model=PaginacionSchema[EvidenciaResponseSchema])
async def listar_evidencias(
    page: int = Query(1, ge=1, description="Numero de pagina"),
    page_size: int = Query(10, ge=1, le=50, description="Elementos por pagina"),
    estado: str | None = Query(None, description="Filtrar por estado"),
    id_aprendiz: int | None = Query(None, description="Filtrar por aprendiz"),
    fecha_desde: datetime | None = Query(None, description="Fecha inicio (ISO)"),
    fecha_hasta: datetime | None = Query(None, description="Fecha fin (ISO)"),
    tipo_formato: str | None = Query(None, description="Tipo de formato"),
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
    return await CoordinadorService.obtener_evidencias_paginadas(
        db,
        page=page,
        page_size=page_size,
        estado=estado,
        id_aprendiz=id_aprendiz,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_formato=tipo_formato
    )


@router.get("/aprendices", response_model=list[AvanceAprendizSchema])
async def listar_aprendices_con_avance(
    programa: str | None = Query(None, description="Filtrar por programa"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/aprendices

    Lista aprendices con su porcentaje de avance.
    Filtro opcional por programa.
    """
    return await CoordinadorService.obtener_avance_aprendices(db, programa=programa)


@router.get("/instructores", response_model=list[InstructorResponseSchema])
async def listar_instructores(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/instructores

    Lista todos los instructores del sistema.
    """
    return await CoordinadorService.obtener_instructores(db)


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


@router.get("/exportar-avance")
async def exportar_avance(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/exportar-avance

    Consolidado de expedientes (RF07): avance por aprendiz en CSV.
    """
    csv_content = await CoordinadorService.exportar_avance_csv(db)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=avance_aprendices_sgep.csv"
        }
    )


@router.get("/alertas", response_model=list[AlertaVencimientoRolSchema])
async def alertas_vencimiento(
    dias: int = Query(7, ge=0, le=90, description="Dias de anticipacion"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    ENDPOINT: GET /api/v1/coordinador/alertas?dias=7

    Vencimientos de TODAS las evidencias pendientes del sistema
    (vista global de seguimiento para la coordinacion).

    Args:
        dias: Ventana de anticipacion (0-90), por defecto 7
        db: Sesion de BD
        usuario: Coordinador autenticado (JWT)

    Returns:
        200: Alertas con nombre_aprendiz ordenadas por urgencia
        403: Si el rol no es coordinador
    """
    return await EvidenciaService.obtener_alertas_rol(
        db=db,
        ids_aprendiz=None,  # EXPLICACIÓN: None => sin filtro, toda la BD
        dias_anticipacion=dias,
    )
