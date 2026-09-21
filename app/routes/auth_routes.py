# app/routes/auth_routes.py
"""
Rutas de autenticación: registro y login de usuarios.
Implementa JWT, hashing de contraseñas, validación.
"""

# EXPLICACIÓN: Importamos las herramientas necesarias de FastAPI y SQLAlchemy
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.usuario import UsuarioBase, Aprendiz
from app.schemas.usuario_schema import RegistroAprendizSchema, LoginSchema, TokenSchema
from datetime import timedelta, datetime
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()

# EXPLICACIÓN: APIRouter agrupa las rutas bajo un prefijo común
# Todas las rutas de este archivo empezarán con /api/v1/auth
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

# EXPLICACIÓN: Configuración JWT para firmar los tokens
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 horas


# ====================================
# SERVICIO DE AUTENTICACIÓN
# ====================================

class AuthService:
    """
    EXPLICACIÓN: Esta clase agrupa toda la lógica de autenticación.
    Separamos la lógica de negocio de las rutas para mantener el código limpio.
    """

    @staticmethod
    async def registrar_aprendiz(db: AsyncSession, datos: RegistroAprendizSchema) -> Aprendiz:
        """
        Registra un nuevo aprendiz en la base de datos.

        Pasos:
        1. Verificar que el email no exista
        2. Crear instancia de Aprendiz
        3. Hashear contraseña (automático en el modelo)
        4. Guardar en BD
        """
        # EXPLICACIÓN: Verificamos si el email ya existe antes de intentar guardar.
        # Usamos 409 Conflict porque es un conflicto de datos existentes.
        stmt_email = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == datos.correo_institucional
        )
        resultado_email = await db.execute(stmt_email)
        if resultado_email.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo institucional ya está registrado"
            )

        # EXPLICACIÓN: Verificamos que el documento no exista tampoco
        stmt_doc = select(UsuarioBase).where(
            UsuarioBase.numero_documento == datos.numero_documento
        )
        resultado_doc = await db.execute(stmt_doc)
        if resultado_doc.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El número de documento ya está registrado"
            )

        # EXPLICACIÓN: Creamos la instancia del Aprendiz. La contraseña se hashea sola
        # gracias al método 'establecer_contrasena' que definimos en el modelo.
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

        # EXPLICACIÓN: Guardamos en la base de datos y confirmamos los cambios
        db.add(nuevo_aprendiz)
        await db.commit()
        await db.refresh(nuevo_aprendiz)

        return nuevo_aprendiz

    @staticmethod
    async def login(db: AsyncSession, credenciales: LoginSchema) -> UsuarioBase:
        """
        Autentica un usuario y retorna sus datos.

        Pasos:
        1. Buscar usuario por email
        2. Verificar contraseña
        3. Retornar usuario si es correcto
        """
        # EXPLICACIÓN: Buscamos al usuario por su correo electrónico
        stmt = select(UsuarioBase).where(
            UsuarioBase.correo_institucional == credenciales.correo_institucional
        )
        resultado = await db.execute(stmt)
        usuario = resultado.scalars().first()

        # EXPLICACIÓN: Si no existe o la contraseña es incorrecta, lanzamos error 401
        if not usuario or not usuario.verificar_contrasena(credenciales.contraseña):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos"
            )

        return usuario


# ====================================
# UTILIDADES
# ====================================

def crear_token_acceso(data: dict, expires_delta: timedelta = None) -> str:
    """
    Crea un JWT token para autenticación.

    Args:
        data: Información a codificar en el token
        expires_delta: Tiempo de expiración personalizado

    Returns:
        Token JWT codificado como string
    """
    to_encode = data.copy()

    # EXPLICACIÓN: Si no especifica expiración, usa el default (24 horas)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # EXPLICACIÓN: Agregamos la fecha de expiración al token
    to_encode.update({"exp": expire})

    # EXPLICACIÓN: Codificamos con JWT usando la clave secreta y algoritmo
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ====================================
# ENDPOINTS
# ====================================

@router.post("/registro", response_model=dict, status_code=status.HTTP_201_CREATED)
async def registro(
    datos: RegistroAprendizSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    ENDPOINT: POST /api/v1/auth/registro

    Registra un nuevo aprendiz en el sistema.

    Args:
        datos: Esquema de registro (email, contraseña, nombre, etc)
        db: Sesión de BD inyectada por FastAPI

    Returns:
        201 Created: Aprendiz creado + token JWT

    Raises:
        409: Email o documento ya existe
        422: Datos inválidos
    """
    # EXPLICACIÓN: Delegamos la lógica al servicio AuthService
    usuario = await AuthService.registrar_aprendiz(db, datos)

    # EXPLICACIÓN: Generamos el token JWT para el usuario creado
    token = crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )

    # EXPLICACIÓN: Retornamos los datos del usuario y el token
    return {
        "mensaje": "Aprendiz registrado exitosamente",
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre_completo,
        "email": usuario.correo_institucional,
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login(
    credenciales: LoginSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    ENDPOINT: POST /api/v1/auth/login

    Autentica usuario y retorna JWT token.

    Args:
        credenciales: Email + contraseña
        db: Sesión de BD

    Returns:
        200 OK: Token JWT + tipo de token

    Raises:
        401: Email o contraseña incorrecta
    """
    # EXPLICACIÓN: Delegamos la lógica al servicio AuthService
    usuario = await AuthService.login(db, credenciales)

    # EXPLICACIÓN: Generamos el token JWT para el usuario autenticado
    token = crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )

    # EXPLICACIÓN: Retornamos el token en el formato esperado
    return {
        "access_token": token,
        "token_type": "bearer"
    }


print("✅ Rutas de autenticación configuradas")
