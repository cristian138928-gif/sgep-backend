# app/routes/notificacion_routes.py
"""
Rutas de notificaciones in-app.
Cualquier rol autenticado solo ve LAS SUYAS (filtro por id_usuario).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.notificacion_schema import (
    ConteoNoLeidasSchema,
    NotificacionResponseSchema,
)
from app.services.notificacion_service import NotificacionService

# EXPLICACIÓN: Sin "/" final + paths relativos => sin redirecciones 307
router = APIRouter(prefix="/api/v1/notificaciones", tags=["Notificaciones"])


@router.get("", response_model=list[NotificacionResponseSchema])
async def listar_notificaciones(
    solo_no_leidas: bool = Query(False, description="Filtra solo las no leídas"),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user),
):
    """
    ENDPOINT: GET /api/v1/notificaciones

    Lista las notificaciones del usuario autenticado (más recientes primero).
    """
    return await NotificacionService.listar(
        db, usuario.id_usuario, solo_no_leidas=solo_no_leidas
    )


@router.get("/no-leidas", response_model=ConteoNoLeidasSchema)
async def contar_no_leidas(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user),
):
    """
    ENDPOINT: GET /api/v1/notificaciones/no-leidas

    Badge de notificaciones sin leer.
    """
    cantidad = await NotificacionService.contar_no_leidas(db, usuario.id_usuario)
    return {"no_leidas": cantidad}


@router.post(
    "/{id_notificacion}/marcar-leida",
    response_model=NotificacionResponseSchema,
)
async def marcar_leida(
    id_notificacion: int,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user),
):
    """
    ENDPOINT: POST /api/v1/notificaciones/{id}/marcar-leida

    Returns:
        200: Notificación marcada
        404: No existe o NO pertenece al usuario (no se filtra existencia)
    """
    return await NotificacionService.marcar_leida(
        db, usuario.id_usuario, id_notificacion
    )


@router.post("/marcar-todas-leidas", response_model=ConteoNoLeidasSchema)
async def marcar_todas_leidas(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(get_current_user),
):
    """
    ENDPOINT: POST /api/v1/notificaciones/marcar-todas-leidas

    Marca todas las notificaciones del usuario como leídas (acción del header).

    Returns:
        200: Conteo final de no leídas (0)
    """
    await NotificacionService.marcar_todas_leidas(db, usuario.id_usuario)
    return {"no_leidas": 0}
