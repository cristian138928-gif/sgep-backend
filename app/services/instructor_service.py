# app/services/instructor_service.py
"""
Servicio de Instructor.
Responsabilidad: Evaluar evidencias, ver historial, estadisticas personales.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import math

from app.models.usuario import (
    Instructor, Evidencia, Retroalimentacion
)


class InstructorService:
    """
    Servicio para el dashboard del instructor.
    
    Funcionalidades:
    - Ver evidencias pendientes de evaluar
    - Evaluar evidencia (aprobar / ajuste)
    - Ver historial de evaluaciones
    - Estadisticas personales
    - Ver perfil
    """

    @staticmethod
    async def obtener_evidencias_pendientes(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        Lista evidencias pendientes de evaluacion.
        
        Returns:
            dict con items paginados y metadata
        """
        page_size = min(page_size, 50)

        stmt = select(Evidencia).where(Evidencia.estado == "Pendiente")
        count_stmt = select(func.count(Evidencia.id_evidencia)).where(
            Evidencia.estado == "Pendiente"
        )

        total = (await db.execute(count_stmt)).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Evidencia.fecha_carga.asc()).offset(offset).limit(page_size)

        resultado = await db.execute(stmt)
        items = resultado.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    @staticmethod
    async def evaluar_evidencia(
        db: AsyncSession,
        id_evidencia: int,
        id_instructor: int,
        estado: str,
        observaciones: str
    ) -> Retroalimentacion:
        """
        Evalua una evidencia y crea retroalimentacion.
        
        Args:
            db: Sesion async
            id_evidencia: ID de la evidencia
            id_instructor: ID del instructor que evalua
            estado: "Aprobada" o "Ajuste Requerido"
            observaciones: Comentarios del instructor
            
        Returns:
            Retroalimentacion creada
            
        Raises:
            404: Evidencia o instructor no encontrado
            400: Estado invalido
            409: Evidencia ya evaluada
        """
        # Validar estado
        if estado not in ["Aprobada", "Ajuste Requerido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado invalido. Debe ser 'Aprobada' o 'Ajuste Requerido'"
            )

        # Verificar evidencia
        stmt_ev = select(Evidencia).where(Evidencia.id_evidencia == id_evidencia)
        resultado_ev = await db.execute(stmt_ev)
        evidencia = resultado_ev.scalars().first()
        
        if not evidencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidencia no encontrada"
            )

        # Verificar que este pendiente
        if evidencia.estado != "Pendiente":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta evidencia ya fue evaluada"
            )

        # Verificar instructor
        stmt_inst = select(Instructor).where(Instructor.id_usuario == id_instructor)
        resultado_inst = await db.execute(stmt_inst)
        instructor = resultado_inst.scalars().first()
        
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor no encontrado"
            )

        # Crear retroalimentacion
        nueva_retro = Retroalimentacion(
            id_evidencia=id_evidencia,
            id_instructor=id_instructor,
            observaciones=observaciones,
            estado_evaluacion=estado
        )

        # Actualizar estado de la evidencia
        evidencia.estado = estado

        db.add(nueva_retro)
        await db.commit()
        await db.refresh(nueva_retro)

        return nueva_retro

    @staticmethod
    async def obtener_historial_evaluaciones(
        db: AsyncSession,
        id_instructor: int,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        Historial de evaluaciones del instructor.
        
        Returns:
            dict con items paginados y metadata
        """
        page_size = min(page_size, 50)

        stmt = select(Retroalimentacion).where(
            Retroalimentacion.id_instructor == id_instructor
        )
        count_stmt = select(func.count(Retroalimentacion.id_retroalimentacion)).where(
            Retroalimentacion.id_instructor == id_instructor
        )

        total = (await db.execute(count_stmt)).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Retroalimentacion.fecha_revision.desc()).offset(offset).limit(page_size)

        resultado = await db.execute(stmt)
        items = resultado.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    @staticmethod
    async def obtener_estadisticas(db: AsyncSession, id_instructor: int) -> dict:
        """
        Estadisticas personales del instructor.
        
        Returns:
            dict con total_evaluadas, aprobadas, ajustes, pendientes
        """
        # Total evaluadas por este instructor
        stmt_total = select(func.count(Retroalimentacion.id_retroalimentacion)).where(
            Retroalimentacion.id_instructor == id_instructor
        )
        total = (await db.execute(stmt_total)).scalar() or 0

        # Aprobadas
        stmt_aprobadas = select(func.count(Retroalimentacion.id_retroalimentacion)).where(
            Retroalimentacion.id_instructor == id_instructor,
            Retroalimentacion.estado_evaluacion == "Aprobada"
        )
        aprobadas = (await db.execute(stmt_aprobadas)).scalar() or 0

        # Ajustes
        stmt_ajustes = select(func.count(Retroalimentacion.id_retroalimentacion)).where(
            Retroalimentacion.id_instructor == id_instructor,
            Retroalimentacion.estado_evaluacion == "Ajuste Requerido"
        )
        ajustes = (await db.execute(stmt_ajustes)).scalar() or 0

        # Pendientes por evaluar
        stmt_pendientes = select(func.count(Evidencia.id_evidencia)).where(
            Evidencia.estado == "Pendiente"
        )
        pendientes = (await db.execute(stmt_pendientes)).scalar() or 0

        return {
            "total_evaluadas": total,
            "aprobadas": aprobadas,
            "ajustes_requeridos": ajustes,
            "pendientes_por_evaluar": pendientes
        }

    @staticmethod
    async def obtener_perfil(db: AsyncSession, id_instructor: int) -> Instructor:
        """
        Obtiene el perfil del instructor.
        
        Returns:
            Instructor con sus datos
        """
        stmt = select(Instructor).where(Instructor.id_usuario == id_instructor)
        resultado = await db.execute(stmt)
        instructor = resultado.scalars().first()
        
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor no encontrado"
            )
        
        return instructor
