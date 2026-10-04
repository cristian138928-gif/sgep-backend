# app/dependencies.py
"""
Dependencias de FastAPI.
Funciones reutilizables para inyección de dependencias (auth, BD, etc.)
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db
from app.models.usuario import UsuarioBase

# EXPLICACIÓN: HTTPBearer extrae el token del header Authorization: Bearer <token>
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UsuarioBase:
    """
    Dependencia para obtener el usuario autenticado.

    Flujo:
    1. Extraer token del header Authorization
    2. Decodificar JWT y validar que sea de tipo access
    3. Obtener email (sub) y buscar usuario en BD
    4. Retornar usuario o error 401

    Uso en endpoints:
        @router.get("/ruta-protegida")
        async def mi_endpoint(usuario: UsuarioBase = Depends(get_current_user)):
            # usuario está autenticado aquí
            return {"email": usuario.correo_institucional}

    Args:
        credentials: Token JWT del header
        db: Sesión de BD

    Returns:
        UsuarioBase: Usuario autenticado

    Raises:
        HTTPException 401: Token inválido o usuario no encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # EXPLICACIÓN: Extraemos el token del header
        token = credentials.credentials

        # EXPLICACIÓN: Decodificamos el JWT (PyJWT valida exp y firma automáticamente)
        # payload contiene: {"sub": "email@email.com", "id": 1, "exp": ..., "type": ...}
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # EXPLICACIÓN: Un refresh token NO autoriza acceso a la API (claims de tipo)
        if payload.get("type") != "access":
            raise credentials_exception

        # EXPLICACIÓN: Obtenemos el email del subject
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

    except PyJWTError:
        # EXPLICACIÓN: Si el token expiró o es inválido
        # EXPLICACIÓN: from None oculta la cadena de error (no aporta al usuario)
        raise credentials_exception from None

    # EXPLICACIÓN: Buscamos el usuario en la BD
    stmt = select(UsuarioBase).where(UsuarioBase.correo_institucional == email)
    resultado = await db.execute(stmt)
    usuario = resultado.scalars().first()

    if usuario is None:
        raise credentials_exception

    return usuario
