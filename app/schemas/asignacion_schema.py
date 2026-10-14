# app/schemas/asignacion_schema.py
"""
Esquemas Pydantic para asignacion de seguimiento.
Vincula aprendices con un instructor seguidor.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AsignacionCreateSchema(BaseModel):
    """Datos para crear una asignacion."""
    id_aprendiz: int
    id_instructor: int


class AsignacionResponseSchema(BaseModel):
    """Respuesta con datos de una asignacion."""
    id_asignacion: int
    id_aprendiz: int
    id_instructor: int
    nombre_aprendiz: str
    nombre_instructor: str
    fecha_asignacion: datetime
    activa: bool

    model_config = ConfigDict(from_attributes=True)
