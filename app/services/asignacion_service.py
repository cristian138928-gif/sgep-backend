# app/services/asignacion_service.py
"""
Servicio de Asignacion de Seguimiento.
Vincula aprendices con un instructor seguidor.
"""


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.usuario import Aprendiz, AsignacionSeguimiento, Instructor, UsuarioBase


class AsignacionService:
    """Logica de negocio para asignaciones aprendiz <-> instructor."""

    @staticmethod
    async def asignar(
        db: AsyncSession, id_aprendiz: int, id_instructor: int
    ) -> AsignacionSeguimiento:
        """
        Asigna un aprendiz a un instructor seguidor.

        Validaciones:
        - Aprendiz debe existir
        - Instructor debe existir
        - No puede haber asignacion activa duplicada
        """
        # Verificar aprendiz
        stmt_ap = select(Aprendiz).where(Aprendiz.id_usuario == id_aprendiz)
        aprendiz = (await db.execute(stmt_ap)).scalar_one_or_none()
        if not aprendiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aprendiz no encontrado"
            )

        # Verificar instructor
        stmt_ins = select(Instructor).where(Instructor.id_usuario == id_instructor)
        instructor = (await db.execute(stmt_ins)).scalar_one_or_none()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor no encontrado"
            )

        # Verificar duplicado activo
        stmt_dup = select(AsignacionSeguimiento).where(
            AsignacionSeguimiento.id_aprendiz == id_aprendiz,
            AsignacionSeguimiento.activa == 1
        )
        existente = (await db.execute(stmt_dup)).scalar_one_or_none()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El aprendiz ya tiene un instructor asignado"
            )

        nueva = AsignacionSeguimiento(
            id_aprendiz=id_aprendiz,
            id_instructor=id_instructor
        )
        db.add(nueva)
        await db.commit()
        await db.refresh(nueva)
        return nueva

    @staticmethod
    async def desasignar(
        db: AsyncSession, id_aprendiz: int
    ) -> dict:
        """
        Desasigna un aprendiz de su instructor (marca activa=0).
        """
        stmt = select(AsignacionSeguimiento).where(
            AsignacionSeguimiento.id_aprendiz == id_aprendiz,
            AsignacionSeguimiento.activa == 1
        )
        asignacion = (await db.execute(stmt)).scalar_one_or_none()
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay asignacion activa para este aprendiz"
            )

        asignacion.activa = 0
        await db.commit()
        return {"mensaje": "Asignacion desactivada correctamente"}

    @staticmethod
    async def listar_aprendices_instructor(
        db: AsyncSession, id_instructor: int
    ) -> list[dict]:
        """
        Lista todos los aprendices asignados a un instructor.
        """
        stmt = (
            select(
                AsignacionSeguimiento,
                Aprendiz.nombre_completo,
                Aprendiz.numero_ficha,
                Aprendiz.programa
            )
            .join(Aprendiz, AsignacionSeguimiento.id_aprendiz == Aprendiz.id_usuario)
            .where(
                AsignacionSeguimiento.id_instructor == id_instructor,
                AsignacionSeguimiento.activa == 1
            )
        )
        resultado = await db.execute(stmt)
        filas = resultado.all()

        return [
            {
                "id_asignacion": f[0].id_asignacion,
                "id_aprendiz": f[0].id_aprendiz,
                "nombre_completo": f[1],
                "numero_ficha": f[2],
                "programa": f[3],
                "fecha_asignacion": f[0].fecha_asignacion
            }
            for f in filas
        ]

    @staticmethod
    async def obtener_instructor_aprendiz(
        db: AsyncSession, id_aprendiz: int
    ) -> dict | None:
        """
        Obtiene el instructor asignado a un aprendiz.
        Retorna None si no tiene asignacion.
        """
        stmt = (
            select(
                AsignacionSeguimiento,
                Instructor.nombre_completo,
                Instructor.centro_formacion
            )
            .join(Instructor, AsignacionSeguimiento.id_instructor == Instructor.id_usuario)
            .where(
                AsignacionSeguimiento.id_aprendiz == id_aprendiz,
                AsignacionSeguimiento.activa == 1
            )
        )
        resultado = await db.execute(stmt)
        fila = resultado.one_or_none()

        if not fila:
            return None

        return {
            "id_instructor": fila[0].id_instructor,
            "nombre_instructor": fila[1],
            "centro_formacion": fila[2],
            "fecha_asignacion": fila[0].fecha_asignacion
        }

    @staticmethod
    async def listar_activas(db: AsyncSession) -> list[dict]:
        """
        Lista todas las asignaciones activas (vista del coordinador).

        Returns:
            dicts con ambos nombres para pintar la tabla sin N+1 queries
        """
        # EXPLICACIÓN: 2 alias de UsuarioBase evitan el SAWarning por
        # herencia joined-table (Aprendiz/Instructor comparten la tabla base)
        ap_alias = aliased(UsuarioBase)
        ins_alias = aliased(UsuarioBase)
        stmt = (
            select(
                AsignacionSeguimiento,
                ap_alias.nombre_completo,
                ins_alias.nombre_completo,
            )
            .join(ap_alias, AsignacionSeguimiento.id_aprendiz == ap_alias.id_usuario)
            .join(ins_alias, AsignacionSeguimiento.id_instructor == ins_alias.id_usuario)
            .where(AsignacionSeguimiento.activa == 1)
            .order_by(AsignacionSeguimiento.fecha_asignacion.desc())
        )
        filas = (await db.execute(stmt)).all()

        return [
            {
                "id_asignacion": f[0].id_asignacion,
                "id_aprendiz": f[0].id_aprendiz,
                "id_instructor": f[0].id_instructor,
                "nombre_aprendiz": f[1],
                "nombre_instructor": f[2],
                "fecha_asignacion": f[0].fecha_asignacion,
                "activa": bool(f[0].activa),
            }
            for f in filas
        ]
