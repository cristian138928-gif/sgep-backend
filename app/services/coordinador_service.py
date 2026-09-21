# app/services/coordinador_service.py
"""
Servicio de Coordinador.
Responsabilidad: Dashboard, estadisticas, supervision de evidencias.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
import math

from app.models.usuario import (
    UsuarioBase, Aprendiz, Evidencia, Retroalimentacion, Instructor
)


class CoordinadorService:
    """
    Servicio para el dashboard del coordinador.
    
    Funcionalidades:
    - Estadisticas generales
    - Listado paginado de evidencias con filtros
    - Avance de aprendices
    - Instructores
    """

    @staticmethod
    async def obtener_estadisticas(db: AsyncSession) -> dict:
        """
        Obtiene estadisticas generales del sistema.
        
        Returns:
            dict con contadores y porcentaje de aprobacion
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

        # Porcentaje de aprobacion
        porcentaje = round((aprobadas / total_evidencias) * 100, 2) if total_evidencias > 0 else 0.0

        return {
            "total_evidencias": total_evidencias,
            "aprobadas": aprobadas,
            "pendientes": pendientes,
            "ajustes_requeridos": ajustes,
            "total_aprendices": total_aprendices,
            "total_instructores": total_instructores,
            "porcentaje_aprobacion": porcentaje
        }

    @staticmethod
    async def obtener_evidencias_paginadas(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        estado: Optional[str] = None,
        id_aprendiz: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        tipo_formato: Optional[str] = None
    ) -> dict:
        """
        Lista evidencias con paginacion y filtros avanzados.
        
        Args:
            db: Sesion async
            page: Numero de pagina (default 1)
            page_size: Elementos por pagina (default 10, max 50)
            estado: Filtrar por estado
            id_aprendiz: Filtrar por aprendiz
            fecha_desde: Fecha inicio de carga
            fecha_hasta: Fecha fin de carga
            tipo_formato: Filtrar por tipo (Bitacora, F023, etc.)
            
        Returns:
            dict con items, total, page, page_size, total_pages
        """
        # Limitar page_size a maximo 50
        page_size = min(page_size, 50)
        
        # Construir query base
        stmt = select(Evidencia)
        count_stmt = select(func.count(Evidencia.id_evidencia))

        # Aplicar filtros
        filtros = []
        if estado:
            filtros.append(Evidencia.estado == estado)
        if id_aprendiz:
            filtros.append(Evidencia.id_aprendiz == id_aprendiz)
        if fecha_desde:
            filtros.append(Evidencia.fecha_carga >= fecha_desde)
        if fecha_hasta:
            filtros.append(Evidencia.fecha_carga <= fecha_hasta)
        if tipo_formato:
            filtros.append(Evidencia.tipo_formato == tipo_formato)

        if filtros:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filtros))
            count_stmt = count_stmt.where(and_(*filtros))

        # Total de resultados (para paginacion)
        total = (await db.execute(count_stmt)).scalar() or 0
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Aplicar paginacion y orden
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Evidencia.fecha_carga.desc()).offset(offset).limit(page_size)

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
    async def obtener_avance_aprendices(
        db: AsyncSession,
        programa: Optional[str] = None
    ) -> List[dict]:
        """
        Obtiene el avance de cada aprendiz.
        
        Args:
            db: Sesion async
            programa: Filtrar por programa (opcional)
            
        Returns:
            Lista de dicts con informacion del aprendiz y su avance
        """
        stmt = select(Aprendiz)
        if programa:
            stmt = stmt.where(Aprendiz.programa.contains(programa))
        
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

    @staticmethod
    async def exportar_evidencias_csv(db: AsyncSession) -> str:
        """
        Exporta todas las evidencias como CSV.
        
        Returns:
            str con contenido CSV
        """
        stmt = select(Evidencia).order_by(Evidencia.fecha_carga.desc())
        resultado = await db.execute(stmt)
        evidencias = resultado.scalars().all()

        # Header CSV
        csv_lines = ["id,titulo,tipo_formato,estado,fecha_carga,fecha_deadline,aprendiz_id"]
        
        for ev in evidencias:
            fecha_carga = ev.fecha_carga.strftime("%Y-%m-%d %H:%M") if ev.fecha_carga else ""
            fecha_deadline = ev.fecha_deadline.strftime("%Y-%m-%d %H:%M") if ev.fecha_deadline else ""
            line = f"{ev.id_evidencia},{ev.titulo},{ev.tipo_formato},{ev.estado},{fecha_carga},{fecha_deadline},{ev.id_aprendiz}"
            csv_lines.append(line)

        return "\n".join(csv_lines)
