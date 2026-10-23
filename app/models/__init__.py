# app/models/__init__.py
"""
EXPLICACIÓN: re-exports de TODAS las entidades => `import app.models`
registra cada tabla en Base.metadata (evita create_all incompleto
cuando un módulo importa solo un subconjunto de modelos).
"""

from app.models.refresh_token import RefreshToken as RefreshToken
from app.models.usuario import (
    Aprendiz as Aprendiz,
)
from app.models.usuario import (
    AsignacionSeguimiento as AsignacionSeguimiento,
)
from app.models.usuario import (
    Base as Base,
)
from app.models.usuario import (
    Coordinador as Coordinador,
)
from app.models.usuario import (
    Evidencia as Evidencia,
)
from app.models.usuario import (
    Instructor as Instructor,
)
from app.models.usuario import (
    Notificacion as Notificacion,
)
from app.models.usuario import (
    Retroalimentacion as Retroalimentacion,
)
from app.models.usuario import (
    UsuarioBase as UsuarioBase,
)

__all__ = [
    "Aprendiz",
    "AsignacionSeguimiento",
    "Base",
    "Coordinador",
    "Evidencia",
    "Instructor",
    "Notificacion",
    "RefreshToken",
    "Retroalimentacion",
    "UsuarioBase",
]
