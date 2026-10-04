# app/schemas/instructor_schema.py
"""
Esquemas Pydantic para dashboard del instructor.
Response models para perfil y estadisticas.
"""

from pydantic import BaseModel, ConfigDict


class EstadisticasInstructorSchema(BaseModel):
    """Estadisticas personales del instructor."""
    total_evaluadas: int
    aprobadas: int
    ajustes_requeridos: int
    pendientes_por_evaluar: int

    model_config = ConfigDict(
        json_schema_extra={"example": {
            "total_evaluadas": 25,
            "aprobadas": 18,
            "ajustes_requeridos": 7,
            "pendientes_por_evaluar": 5
        }},
    )


class InstructorPerfilSchema(BaseModel):
    """Perfil del instructor."""
    id_usuario: int
    nombre_completo: str
    correo_institucional: str
    centro_formacion: str
    especialidad: str

    model_config = ConfigDict(from_attributes=True)
