# app/services/coordinador_service.py
"""
Servicio de Coordinador.
Responsabilidad: Dashboard, estadísticas, supervisión de evidencias.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.models.usuario import (
    UsuarioBase, Aprendiz, Evidencia, Retroalimentacion, Instructor
)


class CoordinadorService:
    """
    Servicio para el dashboard del coordinador.
    
    Funcionalidades:
    - Ver todas las evidencias del sistema
    - Estadísticas generales
    - Listado de aprendices con su avance
    - Filtros por estado, fecha, programa
    """

    @staticmethod
    async def obtener_estadisticas(db: AsyncSession) -> dict:
        """
        Obtiene estadísticas generales del sistema.
        
        Returns:
            dict con total_evidencias, aprobadas, pendientes, ajustes,
                  total_aprendices, total_instructores
        """
        # Total de evidencias
        stmt_total = select(func.count(Evidencia.id_evidencia))
        total_evidencias = (await db.execute(stmt_total)).scalar() or 0

        # Evidencias aprobadas
        stmt_aprobadas = select(func.count(Evidencia.id_evidencia)).where(
            Evidencia.estado == "Aprobada"
        )
        aprobadas = (await db.execute(stmt_aprobadas)).scalar() or 0

        # Evidencias pendientes
        stmt_pendientes = select(func.count(Evidencia.id_evidencia)).where(
            Evidencia.estado == "Pendiente"
        )
        pendientes = (await db.execute(stmt_pendientes)).scalar() or 0

        # Evidencias con ajuste requerido
        stmt_ajustes = select(func.count(Evidencia.id_evidencia)).where(
            Evidencia.estado == "Ajuste Requerido"
        )
        ajustes = (await db.execute(stmt_ajustes)).scalar() or 0

        # Total de aprendices
        stmt_aprendices = select(func.count(Aprendiz.id_usuario))
        total_aprendices = (await db.execute(stmt_aprendices)).scalar() or 0

        # Total de instructores
        stmt_instructores = select(func.count(Instructor.id_usuario))
        total_instructores = (await db.execute(stmt_instructores)).scalar() or 0

        return {
            "total_evidencias": total_evidencias,
            "aprobadas": aprobadas,
            "pendientes": pendientes,
            "ajustes_requeridos": ajustes,
            "total_aprendices": total_aprendices,
            "total_instructores": total_instructores
        }

    @staticmethod
    async def obtener_todas_evidencias(
        db: AsyncSession,
        estado: Optional[str] = None,
        id_aprendiz: Optional[int] = None
    ) -> List[Evidencia]:
        """
        Lista todas las evidencias del sistema (vista coordinador).
        
        Args:
            db: Sesión async
            estado: Filtrar por estado (opcional)
            id_aprendiz: Filtrar por aprendiz (opcional)
            
        Returns:
            Lista de evidencias ordenadas por fecha
        """
        stmt = select(Evidencia)

        if estado:
            stmt = stmt.where(Evidencia.estado == estado)
        if id_aprendiz:
            stmt = stmt.where(Evidencia.id_aprendiz == id_aprendiz)

        stmt = stmt.order_by(Evidencia.fecha_carga.desc())
        resultado = await db.execute(stmt)
        return resultado.scalars().all()

    @staticmethod
    async def obtener_avance_aprendices(db: AsyncSession) -> List[dict]:
        """
        Obtiene el avance de cada aprendiz.
        
        Returns:
            Lista de dicts con información del aprendiz y su avance
        """
        stmt = select(Aprendiz)
        resultado = await db.execute(stmt)
        aprendices = resultado.scalars().all()

        avances = []
        for aprendiz in aprendices:
            # Contar evidencias del aprendiz
            stmt_ev = select(func.count(Evidencia.id_evidencia)).where(
                Evidencia.id_aprendiz == aprendiz.id_usuario
            )
            total = (await db.execute(stmt_ev)).scalar() or 0

            stmt_aprobadas = select(func.count(Evidencia.id_evidencia)).where(
                Evidencia.id_aprendiz == aprendiz.id_usuario,
                Evidencia.estado == "Aprobada"
            )
            aprobadas = (await db.execute(stmt_aprobadas)).scalar() or 0

            porcentaje = round((aprobadas / total) * 100, 2) if total > 0 else 0.0

            avances.append({
                "id_usuario": aprendiz.id_usuario,
                "nombre_completo": aprendiz.nombre_completo,
                "numero_ficha": aprendiz.numero_ficha,
                "programa": aprendiz.programa,
                "total_evidencias": total,
                "aprobadas": aprobadas,
                "porcentaje_avance": porcentaje
            })

        return avances

    @staticmethod
    async def obtener_instructores(db: AsyncSession) -> List[Instructor]:
        """Lista todos los instructores del sistema."""
        stmt = select(Instructor)
        resultado = await db.execute(stmt)
        return resultado.scalars().all()
