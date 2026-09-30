# app/services/evidencia_service.py
"""
Servicio de Evidencias.
Responsabilidad: Gestión completa de evidencias (CRUD + evaluación).
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import (
    Aprendiz,
    Evidencia,
    Instructor,
    Retroalimentacion,
    UsuarioBase,
)


class EvidenciaService:
    """
    Servicio para gestionar evidencias.

    Endpoints que soporta:
    - POST /evidencias/upload (subir PDF)
    - GET /evidencias/mis-evidencias (listar del aprendiz)
    - GET /evidencias/{id} (detalle)
    - PUT /evidencias/{id}/evaluar (instructor evalúa)
    """

    @staticmethod
    async def crear_evidencia(
        db: AsyncSession,
        id_aprendiz: int,
        titulo: str,
        tipo_formato: str,
        ruta_archivo: str,
        fecha_deadline: datetime | None = None
    ) -> Evidencia:
        """
        Crea una nueva evidencia.

        Args:
            db: Sesión async
            id_aprendiz: ID del aprendiz que sube
            titulo: Nombre de la evidencia
            tipo_formato: Tipo (Bitácora, F023, etc.)
            ruta_archivo: Ruta donde se guardó el PDF
            fecha_deadline: Fecha límite (opcional)

        Returns:
            Evidencia creada

        Raises:
            404: Aprendiz no encontrado
        """
        # Verificar que el aprendiz existe
        stmt_aprendiz = select(Aprendiz).where(Aprendiz.id_usuario == id_aprendiz)
        resultado = await db.execute(stmt_aprendiz)
        aprendiz = resultado.scalars().first()

        if not aprendiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aprendiz no encontrado"
            )

        nueva_evidencia = Evidencia(
            id_aprendiz=id_aprendiz,
            titulo=titulo,
            tipo_formato=tipo_formato,
            ruta_archivo_pdf=ruta_archivo,
            estado="Pendiente",
            fecha_deadline=fecha_deadline
        )

        db.add(nueva_evidencia)
        await db.commit()
        await db.refresh(nueva_evidencia)

        return nueva_evidencia

    @staticmethod
    async def obtener_evidencias_aprendiz(
        db: AsyncSession,
        id_aprendiz: int
    ) -> list[Evidencia]:
        """
        Lista todas las evidencias de un aprendiz.

        Args:
            db: Sesión async
            id_aprendiz: ID del aprendiz

        Returns:
            Lista de evidencias ordenadas por fecha (más reciente primero)
        """
        stmt = (
            select(Evidencia)
            .where(Evidencia.id_aprendiz == id_aprendiz)
            .order_by(Evidencia.fecha_carga.desc())
        )
        resultado = await db.execute(stmt)
        return resultado.scalars().all()

    @staticmethod
    async def obtener_evidencia_por_id(
        db: AsyncSession,
        id_evidencia: int
    ) -> Evidencia:
        """
        Obtiene una evidencia por su ID.

        Args:
            db: Sesión async
            id_evidencia: ID de la evidencia

        Returns:
            Evidencia encontrada

        Raises:
            404: Evidencia no encontrada
        """
        stmt = select(Evidencia).where(Evidencia.id_evidencia == id_evidencia)
        resultado = await db.execute(stmt)
        evidencia = resultado.scalars().first()

        if not evidencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidencia no encontrada"
            )

        return evidencia

    @staticmethod
    def verificar_acceso(usuario: UsuarioBase, evidencia: Evidencia) -> None:
        """
        Control de acceso a una evidencia (RBAC + propiedad).

        Args:
            usuario: Usuario autenticado (JWT)
            evidencia: Evidencia solicitada

        Raises:
            403: Sin permiso sobre la evidencia
        """
        # EXPLICACIÓN: coordinador ve todo; aprendiz solo lo suyo; instructor evalúa
        if usuario.rol == "coordinador":
            return
        if usuario.rol == "aprendiz" and evidencia.id_aprendiz == usuario.id_usuario:
            return
        if usuario.rol == "instructor":
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta evidencia",
        )

    @staticmethod
    async def evaluar_evidencia(
        db: AsyncSession,
        id_evidencia: int,
        id_instructor: int,
        estado: str,
        observaciones: str
    ) -> Retroalimentacion:
        """
        Evalúa una evidencia (solo instructores).

        Pasos:
        1. Verificar que la evidencia exista
        2. Verificar que el instructor exista
        3. Validar estado (Aprobada / Ajuste Requerido)
        4. Crear registro de Retroalimentacion
        5. Actualizar estado de la evidencia

        Args:
            db: Sesión async
            id_evidencia: ID de la evidencia a evaluar
            id_instructor: ID del instructor que evalúa
            estado: "Aprobada" o "Ajuste Requerido"
            observaciones: Comentarios del instructor

        Returns:
            Retroalimentacion creada

        Raises:
            404: Evidencia o instructor no encontrado
            400: Estado inválido
        """
        # Validar estado
        if estado not in ["Aprobada", "Ajuste Requerido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado inválido. Debe ser 'Aprobada' o 'Ajuste Requerido'"
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

        # EXPLICACIÓN: Validar que la evidencia no haya sido evaluada previamente
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

        # Crear retroalimentación
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
    async def obtener_retroalimentacion(
        db: AsyncSession,
        id_evidencia: int
    ) -> Retroalimentacion | None:
        """
        Obtiene la retroalimentación de una evidencia.

        Args:
            db: Sesión async
            id_evidencia: ID de la evidencia

        Returns:
            Retroalimentacion o None si no tiene
        """
        stmt = select(Retroalimentacion).where(
            Retroalimentacion.id_evidencia == id_evidencia
        )
        resultado = await db.execute(stmt)
        return resultado.scalars().first()

    @staticmethod
    async def obtener_alertas_vencimiento(
        db: AsyncSession,
        id_aprendiz: int,
        dias_anticipacion: int = 7,
    ) -> list[dict]:
        """
        Alertas de vencimiento de las evidencias pendientes de un aprendiz.

        Reglas:
        - Solo evidencias Pendiente con fecha_deadline definida.
        - "Vencida": deadline ya pasó (dias_restantes < 0).
        - "Por vencer": dentro de los próximos dias_anticipacion días.

        Args:
            db: Sesión async
            id_aprendiz: ID del aprendiz consultado
            dias_anticipacion: Ventana de anticipación en días

        Returns:
            Lista de dicts ordenada por urgencia (más crítica primero)
        """
        return await EvidenciaService._construir_alertas(
            db=db,
            filtro_aprendiz=Evidencia.id_aprendiz == id_aprendiz,
            dias_anticipacion=dias_anticipacion,
            incluir_aprendiz=False,
        )

    @staticmethod
    async def obtener_alertas_rol(
        db: AsyncSession,
        ids_aprendiz: list[int] | None,
        dias_anticipacion: int = 7,
    ) -> list[dict]:
        """
        Alertas de vencimiento para instructor y coordinador.

        A diferencia de la vista del aprendiz, aquí la alerta incluye
        nombre_aprendiz para saber de QUIÉN es la evidencia vencida.

        Args:
            db: Sesión async
            ids_aprendiz: IDs autorizados; None => todo el sistema (coordinador)
            dias_anticipacion: Ventana de anticipación en días

        Returns:
            Lista de dicts con nombre_aprendiz, ordenada por urgencia
        """
        # EXPLICACIÓN: lista vacía del instructor => sin asignaciones, sin alertas
        if ids_aprendiz is not None and not ids_aprendiz:
            return []

        filtro = (
            Evidencia.id_aprendiz.in_(ids_aprendiz)
            if ids_aprendiz is not None
            else True  # EXPLICACIÓN: True equivale a SIN filtro (coordinador)
        )
        return await EvidenciaService._construir_alertas(
            db=db,
            filtro_aprendiz=filtro,
            dias_anticipacion=dias_anticipacion,
            incluir_aprendiz=True,
        )

    @staticmethod
    async def _construir_alertas(
        db: AsyncSession,
        filtro_aprendiz,
        dias_anticipacion: int,
        incluir_aprendiz: bool,
    ) -> list[dict]:
        """
        Constructor único de alertas (evita duplicar la lógica de vencimiento).

        Args:
            db: Sesión async
            filtro_aprendiz: Cláusula WHERE sobre Evidencia.id_aprendiz
            dias_anticipacion: Ventana de anticipación en días
            incluir_aprendiz: Agrega nombre_aprendiz a cada alerta

        Returns:
            Lista de dicts ordenada por urgencia
        """
        # EXPLICACIÓN: Comparamos solo fechas => evita mezclar zonas horarias
        hoy = datetime.now(UTC).date()

        stmt = (
            select(Evidencia, Aprendiz.nombre_completo)
            .join(Aprendiz, Aprendiz.id_usuario == Evidencia.id_aprendiz)
            .where(
                filtro_aprendiz,
                Evidencia.estado == "Pendiente",
                Evidencia.fecha_deadline.is_not(None),
            )
        )
        filas = (await db.execute(stmt)).all()

        alertas: list[dict] = []
        for evidencia, nombre_aprendiz in filas:
            dias_restantes = (evidencia.fecha_deadline.date() - hoy).days

            if dias_restantes < 0:
                estado_alerta = "Vencida"
            elif dias_restantes <= dias_anticipacion:
                estado_alerta = "Por vencer"
            else:
                continue  # EXPLICACIÓN: Fuera de ventana => no es alerta

            alerta = {
                "id_evidencia": evidencia.id_evidencia,
                "titulo": evidencia.titulo,
                "fecha_deadline": evidencia.fecha_deadline,
                "dias_restantes": dias_restantes,
                "estado_alerta": estado_alerta,
            }
            if incluir_aprendiz:
                alerta["nombre_aprendiz"] = nombre_aprendiz
            alertas.append(alerta)

        # EXPLICACIÓN: Orden por urgencia: las vencidas (negativas) primero
        alertas.sort(key=lambda alerta: alerta["dias_restantes"])
        return alertas
