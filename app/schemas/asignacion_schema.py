# app/schemas/asignacion_schema.py
"""
Esquemas Pydantic para asignacion de seguimiento.
Vincula aprendices con un instructor seguidor.
"""

from datetime import datetime

from pydantic import BaseModel


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

    class Config:
        from_attributes = True


class AprendizAsignadoSchema(BaseModel):
    """Aprendiz con info de su asignacion."""
    id_usuario: int
    nombre_completo: str
    numero_ficha: str
    programa: str
    id_instructor_asignado: int | None = None
    nombre_instructor: str | None = None

    class Config:
        from_attributes = True


class InstructorConAprendicesSchema(BaseModel):
    """Instructor con lista de aprendices asignados."""
    id_usuario: int
    nombre_completo: str
    centro_formacion: str
    total_aprendices: int

    class Config:
        from_attributes = True
