# app/services/retroalimentacion_service.py
"""
Servicio de Retroalimentacion independiente.
Permite crear comentarios/evaluaciones sin cambiar estado de la evidencia.
"""


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Evidencia, Instructor, Retroalimentacion


class RetroalimentacionService:
    """Logica para crear retroalimentacion de forma independiente."""

    @staticmethod
    async def crear(
        db: AsyncSession,
        id_evidencia: int,
        id_instructor: int,
        observaciones: str,
        estado_evaluacion: str | None = None
    ) -> Retroalimentacion:
        """
        Crea una retroalimentacion para una evidencia.

        Si se provee estado_evaluacion, tambien actualiza el estado
        de la evidencia (Aprobada / Ajuste Requerido).
        """
        # Verificar evidencia
        stmt_ev = select(Evidencia).where(Evidencia.id_evidencia == id_evidencia)
        evidencia = (await db.execute(stmt_ev)).scalar_one_or_none()
        if not evidencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidencia no encontrada"
            )

        # EXPLICACIÓN: id_evidencia es unique en el modelo; duplicar daría 500 (IntegrityError)
        stmt_dup = select(Retroalimentacion).where(
            Retroalimentacion.id_evidencia == id_evidencia
        )
        if (await db.execute(stmt_dup)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La evidencia ya tiene retroalimentacion registrada"
            )

        # Verificar instructor
        stmt_ins = select(Instructor).where(Instructor.id_usuario == id_instructor)
        instructor = (await db.execute(stmt_ins)).scalar_one_or_none()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor no encontrado"
            )

        nueva = Retroalimentacion(
            id_evidencia=id_evidencia,
            id_instructor=id_instructor,
            observaciones=observaciones,
            estado_evaluacion=estado_evaluacion or evidencia.estado
        )

        # Actualizar estado de evidencia solo si se especifica
        if estado_evaluacion:
            evidencia.estado = estado_evaluacion

        db.add(nueva)
        await db.commit()
        await db.refresh(nueva)
        return nueva

    @staticmethod
    async def obtener_por_id(
        db: AsyncSession, id_retroalimentacion: int
    ) -> Retroalimentacion:
        """Obtiene una retroalimentacion por su ID."""
        stmt = select(Retroalimentacion).where(
            Retroalimentacion.id_retroalimentacion == id_retroalimentacion
        )
        resultado = (await db.execute(stmt)).scalar_one_or_none()
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Retroalimentacion no encontrada"
            )
        return resultado
