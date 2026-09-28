# app/schemas/usuario_schema.py
"""
Esquemas Pydantic: validación de datos para endpoints.
Request/Response models para autenticación.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# ====================================
# ESQUEMAS DE REGISTRO
# ====================================

class RegistroAprendizSchema(BaseModel):
    """
    Validación para registro de aprendiz.

    Campos obligatorios:
    - nombre_completo: Nombre y apellido
    - correo_institucional: Email SENA (validado)
    - contraseña: Mínimo 8 caracteres
    - numero_documento: CC/TI
    - numero_ficha: Ficha de matrícula
    - programa: Programa de formación
    """

    nombre_completo: str = Field(..., min_length=5, max_length=150)
    correo_institucional: EmailStr  # Valida formato email automáticamente
    contraseña: str = Field(..., min_length=8, max_length=100)
    numero_documento: str = Field(..., min_length=6, max_length=20)
    numero_ficha: str = Field(..., min_length=5, max_length=20)
    programa: str = Field(..., min_length=3, max_length=100)

    class Config:
        # Ejemplo para documentación automática en Swagger
        example = {
            "nombre_completo": "Juan Pérez García",
            "correo_institucional": "juan.perez@sena.edu.co",
            "contraseña": "MiContra123!",
            "numero_documento": "1023456789",
            "numero_ficha": "3388939",
            "programa": "ADSO - Análisis y Desarrollo de Software"
        }


# EXPLICACIÓN: Esquemas adicionales para registro de Instructor y Coordinador
class RegistroInstructorSchema(BaseModel):
    """
    Validación para registro de instructor.
    """
    nombre_completo: str = Field(..., min_length=5, max_length=150)
    correo_institucional: EmailStr
    contraseña: str = Field(..., min_length=8, max_length=100)
    numero_documento: str = Field(..., min_length=6, max_length=20)
    centro_formacion: str = Field(..., min_length=5, max_length=150)
    especialidad: str = Field(..., min_length=3, max_length=100)


class RegistroCoordinadorSchema(BaseModel):
    """
    Validación para registro de coordinador.
    """
    nombre_completo: str = Field(..., min_length=5, max_length=150)
    correo_institucional: EmailStr
    contraseña: str = Field(..., min_length=8, max_length=100)
    numero_documento: str = Field(..., min_length=6, max_length=20)
    departamento: str = Field(..., min_length=5, max_length=100)

# ====================================
# ESQUEMAS DE LOGIN
# ====================================

class LoginSchema(BaseModel):
    """
    Validación para login.

    Solo necesita:
    - correo_institucional
    - contraseña
    """

    correo_institucional: EmailStr
    contraseña: str = Field(..., min_length=8)

    class Config:
        example = {
            "correo_institucional": "juan.perez@sena.edu.co",
            "contraseña": "MiContra123!"
        }

# ====================================
# ESQUEMAS DE RESPUESTA
# ====================================

class TokenSchema(BaseModel):
    """
    Respuesta de login/registro: JWT token.
    """

    access_token: str  # El JWT en sí
    token_type: str = "bearer"  # Tipo de token (siempre "bearer")

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }

class AprendizResponseSchema(BaseModel):
    """
    Respuesta de usuario aprendiz (para GET).
    No expone contraseña.
    """

    id_usuario: int
    nombre_completo: str
    correo_institucional: str
    numero_ficha: str
    programa: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True  # Convierte modelos SQLAlchemy a JSON automáticamente
        example = {
            "id_usuario": 1,
            "nombre_completo": "Juan Pérez García",
            "correo_institucional": "juan.perez@sena.edu.co",
            "numero_ficha": "3388939",
            "programa": "ADSO",
            "fecha_creacion": "2025-09-18T10:30:00"
        }

# EXPLICACIÓN: ASCII-only porque las consolas cp1252 no codifican emojis (UnicodeEncodeError)
print("[OK] Esquemas de autenticacion configurados")
