# app/services/auth_service.py
"""
Servicio de Autenticación.
Responsabilidad:Registrar y autenticar usuarios, gestionar JWT.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from jwt import PyJWTError, decode, encode
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.usuario import Aprendiz, Coordinador, Instructor, UsuarioBase
from app.schemas.usuario_schema import (
    LoginSchema,
    RegistroAprendizSchema,
    RegistroCoordinadorSchema,
    RegistroInstructorSchema,
)

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# EXPLICACIÓN: ventana para absorber la carrera de refresh entre pestañas del SPA
REUSE_GRACE_SECONDS = 15


class AuthService:
    """
    Servicio de autenticación.

    Patrón utilizado: Service Layer
    - Separa lógica de negocio de las rutas
    - Facilita testing (mocking de servicios)
    - Promueve reutilización
    """

    @staticmethod
    async def registrar_aprendiz(db: AsyncSession, datos: RegistroAprendizSchema) -> Aprendiz:
        """
        Registra un nuevo aprendiz.

        Pasos:
        1. Verificar que email no exista
        2. Verificar que documento no exista
        3. Crear instancia Aprendiz
        4. Hashear contraseña
        5. Guardar en BD

        Args:
            db: Sesión async de SQLAlchemy
            datos: Esquema de validación de registro

        Returns:
            Aprendiz: Objeto creado

        Raises:
            HTTPException 409: Email o documento ya existe
        """
        # Verificar email único
        stmt_email = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == datos.correo_institucional
        )
        resultado_email = await db.execute(stmt_email)
        if resultado_email.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo institucional ya está registrado"
            )

        # Verificar documento único
        stmt_doc = select(UsuarioBase).where(
            UsuarioBase.numero_documento == datos.numero_documento
        )
        resultado_doc = await db.execute(stmt_doc)
        if resultado_doc.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de documento ya está registrado"
            )

        # Crear Aprendiz (contraseña se hashea en el método establecer_contrasena)
        nuevo_aprendiz = Aprendiz(
            nombre_completo=datos.nombre_completo,
            correo_institucional=datos.correo_institucional,
            numero_documento=datos.numero_documento,
            tipo_documento="CC",
            numero_ficha=datos.numero_ficha,
            programa=datos.programa,
            rol="aprendiz"
        )
        nuevo_aprendiz.establecer_contrasena(datos.contraseña)

        db.add(nuevo_aprendiz)
        await db.commit()
        await db.refresh(nuevo_aprendiz)

        return nuevo_aprendiz

    @staticmethod
    async def registrar_instructor(db: AsyncSession, datos: RegistroInstructorSchema) -> Instructor:
        """
        Registra un nuevo instructor.
        """
        # Verificar email único
        stmt_email = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == datos.correo_institucional
        )
        resultado_email = await db.execute(stmt_email)
        if resultado_email.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo institucional ya está registrado"
            )

        # Verificar documento único
        stmt_doc = select(UsuarioBase).where(
            UsuarioBase.numero_documento == datos.numero_documento
        )
        resultado_doc = await db.execute(stmt_doc)
        if resultado_doc.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de documento ya está registrado"
            )

        # Crear Instructor
        nuevo_instructor = Instructor(
            nombre_completo=datos.nombre_completo,
            correo_institucional=datos.correo_institucional,
            numero_documento=datos.numero_documento,
            tipo_documento="CC",
            centro_formacion=datos.centro_formacion,
            especialidad=datos.especialidad,
            rol="instructor"
        )
        nuevo_instructor.establecer_contrasena(datos.contraseña)

        db.add(nuevo_instructor)
        await db.commit()
        await db.refresh(nuevo_instructor)

        return nuevo_instructor

    @staticmethod
    async def registrar_coordinador(
        db: AsyncSession, datos: RegistroCoordinadorSchema
    ) -> Coordinador:
        """
        Registra un nuevo coordinador.
        """
        # Verificar email único
        stmt_email = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == datos.correo_institucional
        )
        resultado_email = await db.execute(stmt_email)
        if resultado_email.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo institucional ya está registrado"
            )

        # Verificar documento único
        stmt_doc = select(UsuarioBase).where(
            UsuarioBase.numero_documento == datos.numero_documento
        )
        resultado_doc = await db.execute(stmt_doc)
        if resultado_doc.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de documento ya está registrado"
            )

        # Crear Coordinador
        nuevo_coordinador = Coordinador(
            nombre_completo=datos.nombre_completo,
            correo_institucional=datos.correo_institucional,
            numero_documento=datos.numero_documento,
            tipo_documento="CC",
            departamento=datos.departamento,
            rol="coordinador"
        )
        nuevo_coordinador.establecer_contrasena(datos.contraseña)

        db.add(nuevo_coordinador)
        await db.commit()
        await db.refresh(nuevo_coordinador)

        return nuevo_coordinador

    @staticmethod
    async def login(db: AsyncSession, credenciales: LoginSchema) -> UsuarioBase:
        """
        Autentica usuario por email y contraseña.

        Args:
            db: Sesión async
            credenciales: Email + contraseña

        Returns:
            UsuarioBase: Usuario autenticado

        Raises:
            HTTPException 401: Credenciales inválidas
        """
        stmt = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == credenciales.correo_institucional
        )
        resultado = await db.execute(stmt)
        usuario = resultado.scalars().first()

        if not usuario or not usuario.verificar_contrasena(credenciales.contraseña):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos"
            )

        return usuario

    @staticmethod
    def crear_token_acceso(data: dict, expires_delta: timedelta = None) -> str:
        """
        Genera JWT de ACCESO (type=access, corta duración).

        Args:
            data: Datos a codificar (sub, id, etc.)
            expires_delta: Tiempo de expiración custom

        Returns:
            str: Token JWT codificado
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # EXPLICACIÓN: El claim "type" separa access de refresh (impide usar uno como otro)
        to_encode.update({"exp": expire, "type": "access"})
        return encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def crear_token_refresh(data: dict) -> str:
        """
        Genera JWT de REFRESH (type=refresh, larga duración).

        EXPLICACIÓN: No da acceso a la API; solo sirve para canjear
        un nuevo par de tokens en POST /auth/refresh.
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    async def crear_par_tokens(db: AsyncSession, usuario: UsuarioBase) -> dict[str, str]:
        """
        Devuelve el par {access_token, refresh_token, token_type} y persiste
        el jti del refresh en BD (habilita detección de reuso).
        """
        # EXPLICACIÓN: El claim "rol" permite guards de rutas en el SPA sin /me extra
        jti = str(uuid4())
        expira_en = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        datos = {
            "sub": usuario.correo_institucional,
            "id": usuario.id_usuario,
            "rol": usuario.rol,
            "jti": jti,
        }
        db.add(RefreshToken(jti=jti, id_usuario=usuario.id_usuario, expira_en=expira_en))
        await db.commit()
        return {
            "access_token": AuthService.crear_token_acceso(datos),
            "refresh_token": AuthService.crear_token_refresh(datos),
            "token_type": "bearer",
        }

    @staticmethod
    async def refrescar_acceso(db: AsyncSession, refresh_token: str) -> dict[str, str]:
        """
        Canjea un refresh token por un par nuevo (rotación con detección de reuso).

        EXPLICACIÓN: si un jti ya canjeado vuelve a aparecer, alguien lo usó
        dos veces => posible robo => matamos TODOS los refresh del usuario.

        Args:
            db: Sesión async
            refresh_token: Token de tipo refresh

        Returns:
            dict: Nuevo par de tokens

        Raises:
            HTTPException 401: Token inválido, expirado, de tipo incorrecto,
                             reusado o usuario eliminado
        """
        invalido = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = decode(
                refresh_token, settings.secret_key, algorithms=[settings.algorithm]
            )
        except PyJWTError:
            raise invalido from None

        # EXPLICACIÓN: Un access token intentando canjear → 401 (claims de tipo)
        if payload.get("type") != "refresh":
            raise invalido

        email = payload.get("sub")
        if email is None:
            raise invalido

        # EXPLICACIÓN: El usuario debe seguir existiendo (cuenta borrada = token muerto)
        stmt = select(UsuarioBase).where(UsuarioBase.correo_institucional == email)
        resultado = await db.execute(stmt)
        usuario = resultado.scalars().first()
        if usuario is None:
            raise invalido

        # EXPLICACIÓN: tokens emitidos antes de esta versión no tienen jti => re-login
        jti = payload.get("jti")
        if jti is None:
            raise invalido

        stmt_jti = select(RefreshToken).where(RefreshToken.jti == jti)
        registro = (await db.execute(stmt_jti)).scalars().first()

        # EXPLICACIÓN: sin registro => nunca emitido o ya purgado => mismo caso
        if registro is not None and registro.usado:
            usada_en = registro.usada_en
            if usada_en is not None and usada_en.tzinfo is None:
                # EXPLICACIÓN: SQLite devuelve naive; asumimos UTC (los writes son UTC)
                usada_en = usada_en.replace(tzinfo=UTC)
            # EXPLICACIÓN: gracia de 15s => carrera benigna entre pestañas (NO es robo)
            if (
                usada_en is not None
                and (datetime.now(UTC) - usada_en).total_seconds() <= REUSE_GRACE_SECONDS
            ):
                return await AuthService.crear_par_tokens(db, usuario)
            # EXPLICACIÓN: reuso pasado la gracia => purgamos TODA la cadena del usuario
            await db.execute(
                delete(RefreshToken).where(RefreshToken.id_usuario == usuario.id_usuario)
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reusado; sesiones invalidadas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if registro is None:
            await db.execute(
                delete(RefreshToken).where(RefreshToken.id_usuario == usuario.id_usuario)
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reusado; sesiones invalidadas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # EXPLICACIÓN: housekeeping — los expirados del usuario ya no sirven
        registro.usado = 1
        registro.usada_en = datetime.now(UTC)
        # EXPLICACIÓN: synchronize_session=False evita que SQLAlchemy evalúe la
        # comparación de fechas en memoria (SQLite guarda naive y now() es aware)
        await db.execute(
            delete(RefreshToken)
            .where(
                RefreshToken.id_usuario == usuario.id_usuario,
                RefreshToken.expira_en < datetime.now(UTC),
            )
            .execution_options(synchronize_session=False)
        )
        await db.commit()

        return await AuthService.crear_par_tokens(db, usuario)
