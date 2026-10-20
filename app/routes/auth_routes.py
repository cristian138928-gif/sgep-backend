# app/routes/auth_routes.py
"""
Rutas de autenticación: registro y login de usuarios.
Implementa JWT, hashing de contraseñas, validación.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies import get_current_user
from app.models.usuario import UsuarioBase
from app.schemas.usuario_schema import (
    LoginSchema,
    PerfilUsuarioSchema,
    RefreshTokenSchema,
    RegistroAprendizSchema,
    RegistroCoordinadorSchema,
    RegistroInstructorSchema,
    TokenSchema,
)
from app.security.rate_limit import rate_limit_auth
from app.services.auth_service import AuthService

# EXPLICACIÓN: APIRouter agrupa las rutas bajo un prefijo común
# Todas las rutas de este archivo empezarán con /api/v1/auth
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


# ====================================
# ENDPOINTS
# ====================================

@router.post("/registro", response_model=dict, status_code=status.HTTP_201_CREATED)
async def registro(
    datos: RegistroAprendizSchema,
    db: AsyncSession = Depends(get_db),
    _limite: None = Depends(rate_limit_auth),
):
    """
    ENDPOINT: POST /api/v1/auth/registro

    Registra un nuevo aprendiz en el sistema.

    Args:
        datos: Esquema de registro (email, contraseña, nombre, etc)
        db: Sesión de BD inyectada por FastAPI

    Returns:
        201 Created: Aprendiz creado + par de tokens JWT

    Raises:
        409: Email o documento ya existe
        422: Datos inválidos
        429: Límite de intentos por IP superado
    """
    # EXPLICACIÓN: Delegamos la lógica al servicio AuthService
    usuario = await AuthService.registrar_aprendiz(db, datos)

    # EXPLICACIÓN: Retornamos los datos del usuario y el par de tokens
    return {
        "mensaje": "Aprendiz registrado exitosamente",
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre_completo,
        "email": usuario.correo_institucional,
        **await AuthService.crear_par_tokens(db, usuario),
    }


@router.post("/registro-instructor", response_model=dict, status_code=status.HTTP_201_CREATED)
async def registro_instructor(
    datos: RegistroInstructorSchema,
    db: AsyncSession = Depends(get_db),
    _limite: None = Depends(rate_limit_auth),
):
    """
    ENDPOINT: POST /api/v1/auth/registro-instructor

    Registra un nuevo instructor en el sistema.
    """
    usuario = await AuthService.registrar_instructor(db, datos)

    return {
        "mensaje": "Instructor registrado exitosamente",
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre_completo,
        "email": usuario.correo_institucional,
        **await AuthService.crear_par_tokens(db, usuario),
    }


@router.post("/registro-coordinador", response_model=dict, status_code=status.HTTP_201_CREATED)
async def registro_coordinador(
    datos: RegistroCoordinadorSchema,
    db: AsyncSession = Depends(get_db),
    _limite: None = Depends(rate_limit_auth),
):
    """
    ENDPOINT: POST /api/v1/auth/registro-coordinador

    Registra un nuevo coordinador en el sistema.
    """
    usuario = await AuthService.registrar_coordinador(db, datos)

    return {
        "mensaje": "Coordinador registrado exitosamente",
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre_completo,
        "email": usuario.correo_institucional,
        **await AuthService.crear_par_tokens(db, usuario),
    }


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login(
    credenciales: LoginSchema,
    db: AsyncSession = Depends(get_db),
    _limite: None = Depends(rate_limit_auth),
):
    """
    ENDPOINT: POST /api/v1/auth/login

    Autentica usuario y retorna el par de JWT (access + refresh).

    Args:
        credenciales: Email + contraseña
        db: Sesión de BD

    Returns:
        200 OK: Par de tokens + tipo de token

    Raises:
        401: Email o contraseña incorrecta
        429: Límite de intentos por IP superado
    """
    # EXPLICACIÓN: Delegamos la lógica al servicio AuthService
    usuario = await AuthService.login(db, credenciales)

    return await AuthService.crear_par_tokens(db, usuario)


@router.post("/refresh", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def refresh(
    datos: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db),
    _limite: None = Depends(rate_limit_auth),
):
    """
    ENDPOINT: POST /api/v1/auth/refresh

    Canjea un refresh token por un par nuevo (rotación con detección de reuso).
    Reusar un token ya canjeado invalida TODA la cadena del usuario (posible robo).

    Returns:
        200 OK: Nuevo par de tokens

    Raises:
        401: Refresh token inválido, expirado o de tipo incorrecto
        429: Límite de intentos por IP superado
    """
    return await AuthService.refrescar_acceso(db, datos.refresh_token)


@router.get("/me", response_model=PerfilUsuarioSchema, status_code=status.HTTP_200_OK)
async def perfil_actual(usuario: UsuarioBase = Depends(get_current_user)):
    """
    ENDPOINT: GET /api/v1/auth/me

    Perfil del usuario autenticado (nombre + rol) para el frontend.

    Returns:
        200: Perfil del usuario
        401: Sin token o token inválido/expirado
    """
    return usuario
