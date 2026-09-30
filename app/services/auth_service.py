# app/services/auth_service.py
"""
Servicio de Autenticación.
Responsabilidad:Registrar y autenticar usuarios, gestionar JWT.
"""

import os
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Aprendiz, Coordinador, Instructor, UsuarioBase
from app.schemas.usuario_schema import (
    LoginSchema,
    RegistroAprendizSchema,
    RegistroCoordinadorSchema,
    RegistroInstructorSchema,
)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 horas


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
        Genera JWT token.

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

        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
