# app/schemas/coordinador_schema.py
"""
Esquemas Pydantic para dashboard del coordinador.
Response models para estadisticas, supervision, paginacion.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginacionSchema(BaseModel, Generic[T]):
    """Respuesta paginada generica."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class EstadisticasSchema(BaseModel):
    """Estadisticas generales del sistema."""
    total_evidencias: int
    aprobadas: int
    pendientes: int
    ajustes_requeridos: int
    total_aprendices: int
    total_instructores: int
    porcentaje_aprobacion: float

    class Config:
        example = {
            "total_evidencias": 45,
            "aprobadas": 30,
            "pendientes": 10,
            "ajustes_requeridos": 5,
            "total_aprendices": 20,
            "total_instructores": 5,
            "porcentaje_aprobacion": 66.67
        }


class AvanceAprendizSchema(BaseModel):
    """Avance de un aprendiz especifico."""
    id_usuario: int
    nombre_completo: str
    numero_ficha: str
    programa: str
    total_evidencias: int
    aprobadas: int
    porcentaje_avance: float

    class Config:
        from_attributes = True
        example = {
            "id_usuario": 1,
            "nombre_completo": "Juan Perez",
            "numero_ficha": "3388939",
            "programa": "ADSO",
            "total_evidencias": 10,
            "aprobadas": 7,
            "porcentaje_avance": 70.0
        }


class InstructorResponseSchema(BaseModel):
    """Informacion de un instructor."""
    id_usuario: int
    nombre_completo: str
    correo_institucional: str
    centro_formacion: str
    especialidad: str

    class Config:
        from_attributes = True
