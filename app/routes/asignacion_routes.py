# app/routes/asignacion_routes.py
"""
Rutas de asignacion de seguimiento.
Vincula aprendices con instructores seguidores.
Solo coordinadores pueden gestionar asignaciones.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.asignacion_schema import (
    AsignacionCreateSchema,
    AsignacionResponseSchema,
)
from app.services.asignacion_service import AsignacionService

router = APIRouter(prefix="/api/v1/asignaciones", tags=["Asignaciones"])


async def verificar_coordinador(
    usuario: UsuarioBase = Depends(get_current_user)
) -> UsuarioBase:
    """Solo coordinadores gestionan asignaciones."""
    if usuario.rol != "coordinador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los coordinadores pueden gestionar asignaciones"
        )
    return usuario


@router.post(
    "/",
    response_model=AsignacionResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def crear_asignacion(
    datos: AsignacionCreateSchema,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    POST /api/v1/asignaciones/

    Asigna un aprendiz a un instructor seguidor.
    """
    asignacion = await AsignacionService.asignar(
        db, datos.id_aprendiz, datos.id_instructor
    )
    # Enriquecer respuesta con nombres
    from sqlalchemy import select
    from app.models.usuario import Aprendiz, Instructor

    stmt_ap = select(Aprendiz).where(Aprendiz.id_usuario == datos.id_aprendiz)
    ap = (await db.execute(stmt_ap)).scalar_one()
    stmt_ins = select(Instructor).where(Instructor.id_usuario == datos.id_instructor)
    ins = (await db.execute(stmt_ins)).scalar_one()

    return AsignacionResponseSchema(
        id_asignacion=asignacion.id_asignacion,
        id_aprendiz=asignacion.id_aprendiz,
        id_instructor=asignacion.id_instructor,
        nombre_aprendiz=ap.nombre_completo,
        nombre_instructor=ins.nombre_completo,
        fecha_asignacion=asignacion.fecha_asignacion,
        activa=bool(asignacion.activa)
    )


@router.delete("/{id_aprendiz}")
async def desasignar_aprendiz(
    id_aprendiz: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    DELETE /api/v1/asignaciones/{id_aprendiz}

    Desasigna un aprendiz de su instructor.
    """
    return await AsignacionService.desasignar(db, id_aprendiz)


@router.get("/instructor/{id_instructor}")
async def listar_aprendices_del_instructor(
    id_instructor: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_coordinador)
):
    """
    GET /api/v1/asignaciones/instructor/{id_instructor}

    Lista aprendices asignados a un instructor.
    """
    return await AsignacionService.listar_aprendices_instructor(db, id_instructor)


@router.get("/aprendiz/{id_aprendiz}")
async def ver_instructor_asignado(
    id_aprendiz: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user)
):
    """
    GET /api/v1/asignaciones/aprendiz/{id_aprendiz}

    Muestra el instructor asignado a un aprendiz.
    Accesible para coordinadores y el propio aprendiz.
    """
    if usuario.rol not in ("coordinador", "aprendiz"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado"
        )
    if usuario.rol == "aprendiz" and usuario.id_usuario != id_aprendiz:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes ver tu propia asignacion"
        )

    resultado = await AsignacionService.obtener_instructor_aprendiz(db, id_aprendiz)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay instructor asignado a este aprendiz"
        )
    return resultado
