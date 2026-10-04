# app/services/notificacion_service.py
"""
Servicio de notificaciones in-app y alertas de vencimiento materializadas.

EXPLICACIÓN: Centraliza la creación para garantizar dos reglas en un solo
lugar: (1) dedupe de alertas de vencimiento, (2) ownership al marcar leída.
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Notificacion
from app.schemas.notificacion_schema import NotificacionResponseSchema
from app.services.evidencia_service import EvidenciaService


class NotificacionService:
    """Service Layer de notificaciones (CRUD + generación de alertas)."""

    @staticmethod
    async def crear(
        db: AsyncSession,
        *,
        id_usuario: int,
        mensaje: str,
        tipo: str,
        id_evidencia: int | None = None,
    ) -> Notificacion:
        """
        Crea una notificación para un usuario.

        Args:
            db: Sesión async
            id_usuario: Destinatario
            mensaje: Texto visible (máx 300)
            tipo: evaluacion | vencimiento | sistema
            id_evidencia: Evidencia relacionada (opcional)

        Returns:
            Notificacion creada
        """
        notificacion = Notificacion(
            id_usuario=id_usuario,
            mensaje=mensaje[:300],
            tipo=tipo,
            id_evidencia=id_evidencia,
        )
        db.add(notificacion)
        await db.commit()
        await db.refresh(notificacion)
        return notificacion

    @staticmethod
    async def existe_alerta_abierta(
        db: AsyncSession, *, id_usuario: int, tipo: str, id_evidencia: int | None
    ) -> bool:
        """True si ya hay una notificación de ese tipo SIN leer para la evidencia."""
        stmt = select(Notificacion.id_notificacion).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.tipo == tipo,
            Notificacion.id_evidencia == id_evidencia,
            Notificacion.leida == 0,
        )
        return (await db.execute(stmt)).first() is not None

    @staticmethod
    async def listar(
        db: AsyncSession,
        id_usuario: int,
        solo_no_leidas: bool = False,
    ) -> list[NotificacionResponseSchema]:
        """Lista las notificaciones de UN usuario (más recientes primero)."""
        stmt = (
            select(Notificacion)
            .where(Notificacion.id_usuario == id_usuario)
            .order_by(Notificacion.fecha_creacion.desc())
        )
        if solo_no_leidas:
            stmt = stmt.where(Notificacion.leida == 0)

        resultados = (await db.execute(stmt)).scalars().all()
        return [NotificacionResponseSchema.model_validate(n) for n in resultados]

    @staticmethod
    async def contar_no_leidas(db: AsyncSession, id_usuario: int) -> int:
        """Cuenta notificaciones sin leer (badge del header)."""
        stmt = select(func.count(Notificacion.id_notificacion)).where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.leida == 0,
        )
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def marcar_leida(
        db: AsyncSession, id_usuario: int, id_notificacion: int
    ) -> NotificacionResponseSchema:
        """
        Marca una notificación como leída.

        EXPLICACIÓN: Se filtra también por id_usuario => nadie puede marcar
        notificaciones ajenas (404 en vez de 403 para no filtrar existencia).
        """
        notificacion = (
            await db.execute(
                select(Notificacion).where(
                    Notificacion.id_notificacion == id_notificacion,
                    Notificacion.id_usuario == id_usuario,
                )
            )
        ).scalars().first()

        if not notificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada",
            )

        notificacion.leida = 1
        await db.commit()
        await db.refresh(notificacion)
        return NotificacionResponseSchema.model_validate(notificacion)

    @staticmethod
    async def marcar_todas_leidas(db: AsyncSession, id_usuario: int) -> int:
        """
        Marca TODAS las notificaciones del usuario como leídas.

        EXPLICACIÓN: UPDATE en lote => 1 sentencia SQL en vez de N commits.

        Returns:
            int: Cantidad de notificaciones marcadas
        """
        resultado = await db.execute(
            update(Notificacion)
            .where(
                Notificacion.id_usuario == id_usuario,
                Notificacion.leida == 0,
            )
            .values(leida=1)
        )
        await db.commit()
        return resultado.rowcount or 0

    @staticmethod
    async def generar_alertas_vencimiento(
        db: AsyncSession, dias_anticipacion: int = 7
    ) -> int:
        """
        Materializa las alertas de vencimiento como notificaciones.

        EXPLICACIÓN: Reutiliza _construir_alertas (misma regla de negocio que
        los endpoints /alertas) y deduplica por evidencia+tipo no leída.

        Returns:
            int: Cantidad de notificaciones creadas
        """
        alertas = await EvidenciaService.obtener_alertas_rol(
            db=db,
            ids_aprendiz=None,  # toda la BD
            dias_anticipacion=dias_anticipacion,
        )

        creadas = 0
        for alerta in alertas:
            if alerta["estado_alerta"] == "Vencida":
                mensaje = (
                    f"Vencida: '{alerta['titulo']}' superó su fecha límite "
                    f"({alerta['fecha_deadline']:%Y-%m-%d})"
                )
            else:
                mensaje = (
                    f"Por vencer: '{alerta['titulo']}' vence en "
                    f"{alerta['dias_restantes']} día(s)"
                )

            # EXPLICACIÓN: Si ya hay alerta abierta NO se cuenta ni se duplica
            ya_existe = await NotificacionService.existe_alerta_abierta(
                db,
                id_usuario=alerta["id_aprendiz"],
                tipo="vencimiento",
                id_evidencia=alerta["id_evidencia"],
            )
            if ya_existe:
                continue

            await NotificacionService.crear(
                db,
                id_usuario=alerta["id_aprendiz"],
                mensaje=mensaje,
                tipo="vencimiento",
                id_evidencia=alerta["id_evidencia"],
            )
            creadas += 1

        return creadas
