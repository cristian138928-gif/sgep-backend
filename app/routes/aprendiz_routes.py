# app/routes/aprendiz_routes.py
"""
Rutas del dashboard de aprendiz.
Consulta de avance, evidencias propias.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase, Aprendiz, Evidencia
from app.schemas.coordinador_schema import AvanceAprendizSchema

router = APIRouter(prefix="/api/v1/aprendiz", tags=["Aprendiz"])


async def verificar_aprendiz(
    usuario: UsuarioBase = Depends(get_current_user)
) -> UsuarioBase:
    """Dependencia que verifica que el usuario sea aprendiz."""
    if usuario.rol != "aprendiz":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los aprendices pueden acceder a este recurso"
        )
    return usuario


@router.get("/avance", response_model=AvanceAprendizSchema)
async def mi_avance(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioBase = Depends(verificar_aprendiz)
):
    """
    ENDPOINT: GET /api/v1/aprendiz/avance

    Obtiene el porcentaje de avance del aprendiz autenticado.
    Calcula: (evidencias aprobadas / total evidencias) * 100
    """
    stmt = select(Aprendiz).where(Aprendiz.id_usuario == usuario.id_usuario)
    resultado = await db.execute(stmt)
    aprendiz = resultado.scalars().first()

    if not aprendiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aprendiz no encontrado"
        )

    stmt_total = select(func.count(Evidencia.id_evidencia)).where(
        Evidencia.id_aprendiz == usuario.id_usuario
    )
    total = (await db.execute(stmt_total)).scalar() or 0

    stmt_aprobadas = select(func.count(Evidencia.id_evidencia)).where(
        Evidencia.id_aprendiz == usuario.id_usuario,
        Evidencia.estado == "Aprobada"
    )
    aprobadas = (await db.execute(stmt_aprobadas)).scalar() or 0

    porcentaje = round((aprobadas / total) * 100, 2) if total > 0 else 0.0

    return {
        "id_usuario": aprendiz.id_usuario,
        "nombre_completo": aprendiz.nombre_completo,
        "numero_ficha": aprendiz.numero_ficha,
        "programa": aprendiz.programa,
        "total_evidencias": total,
        "aprobadas": aprobadas,
        "porcentaje_avance": porcentaje
    }
