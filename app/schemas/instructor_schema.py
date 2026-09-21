# app/schemas/instructor_schema.py
"""
Esquemas Pydantic para dashboard del instructor.
Response models para evaluaciones y estadisticas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EstadisticasInstructorSchema(BaseModel):
    """Estadisticas personales del instructor."""
    total_evaluadas: int
    aprobadas: int
    ajustes_requeridos: int
    pendientes_por_evaluar: int

    class Config:
        example = {
            "total_evaluadas": 25,
            "aprobadas": 18,
            "ajustes_requeridos": 7,
            "pendientes_por_evaluar": 5
        }


class InstructorPerfilSchema(BaseModel):
    """Perfil del instructor."""
    id_usuario: int
    nombre_completo: str
    correo_institucional: str
    centro_formacion: str
    especialidad: str

    class Config:
        from_attributes = True


class EvaluarEvidenciaSchema(BaseModel):
    """Schema para evaluar evidencia."""
    estado: str = Field(..., pattern="^(Aprobada|Ajuste Requerido)$")
    observaciones: str = Field(..., min_length=10, max_length=1000)

    class Config:
        example = {
            "estado": "Aprobada",
            "observaciones": "Buena bitacora, cumple con los requisitos minimos."
        }


class RetroalimentacionResponseSchema(BaseModel):
    """Respuesta de retroalimentacion."""
    id_retroalimentacion: int
    id_evidencia: int
    id_instructor: int
    observaciones: str
    estado_evaluacion: str
    fecha_revision: datetime

    class Config:
        from_attributes = True
