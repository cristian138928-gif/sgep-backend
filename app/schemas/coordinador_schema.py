# app/schemas/coordinador_schema.py
"""
Esquemas Pydantic para dashboard del coordinador.
Response models para estadisticas, supervision, paginacion.
"""

from pydantic import BaseModel, ConfigDict


class PaginacionSchema[T](BaseModel):
    """Respuesta paginada generica (PEP 695: type params nativos de Python 3.12)."""
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

    model_config = ConfigDict(
        json_schema_extra={"example": {
            "total_evidencias": 45,
            "aprobadas": 30,
            "pendientes": 10,
            "ajustes_requeridos": 5,
            "total_aprendices": 20,
            "total_instructores": 5,
            "porcentaje_aprobacion": 66.67
        }},
    )


class AvanceAprendizSchema(BaseModel):
    """Avance de un aprendiz especifico."""
    id_usuario: int
    nombre_completo: str
    numero_ficha: str
    programa: str
    total_evidencias: int
    aprobadas: int
    porcentaje_avance: float

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id_usuario": 1,
            "nombre_completo": "Juan Perez",
            "numero_ficha": "3388939",
            "programa": "ADSO",
            "total_evidencias": 10,
            "aprobadas": 7,
            "porcentaje_avance": 70.0
        }},
    )


class InstructorResponseSchema(BaseModel):
    """Informacion de un instructor."""
    id_usuario: int
    nombre_completo: str
    correo_institucional: str
    centro_formacion: str
    especialidad: str

    model_config = ConfigDict(from_attributes=True)
