# app/routes/auth_routes.py
"""
Rutas de autenticación: registro y login de usuarios.
Implementa JWT, hashing de contraseñas, validación.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.usuario_schema import RegistroAprendizSchema, LoginSchema, TokenSchema
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
    token = AuthService.crear_token_acceso(
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
    token = AuthService.crear_token_acceso(
        data={"sub": usuario.correo_institucional, "id": usuario.id_usuario}
    )

    # EXPLICACIÓN: Retornamos el token en el formato esperado
    return {
        "access_token": token,
        "token_type": "bearer"
    }
