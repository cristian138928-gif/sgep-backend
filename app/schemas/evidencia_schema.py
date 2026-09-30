# app/schemas/evidencia_schema.py
"""
Esquemas Pydantic para evidencias.
Request/Response models para endpoints de evidencias.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ====================================
# ESQUEMAS DE REQUEST
# ====================================

class EvidenciaCreateSchema(BaseModel):
    """
    Validación para crear evidencia (upload).
    
    Campos:
    - titulo: Nombre de la bitácora
    - tipo_formato: Tipo de documento
    - fecha_deadline: Fecha límite (opcional)
    """
    titulo: str = Field(..., min_length=3, max_length=200)
    tipo_formato: str = Field(..., min_length=2, max_length=50)
    fecha_deadline: Optional[datetime] = None

    class Config:
        example = {
            "titulo": "Bitácora Semana 3",
            "tipo_formato": "Bitácora",
            "fecha_deadline": "2025-10-15T23:59:59"
        }


class EvaluarEvidenciaSchema(BaseModel):
    """
    Validación para evaluar evidencia (instructor).
    
    Campos:
    - estado: Aprobada / Ajuste Requerido
    - observaciones: Comentarios del instructor
    """
    estado: str = Field(..., pattern="^(Aprobada|Ajuste Requerido)$")
    observaciones: str = Field(..., min_length=10, max_length=1000)

    class Config:
        example = {
            "estado": "Aprobada",
            "observaciones": "Buena bitácora, cumple con los requisitos mínimos."
        }


# ====================================
# ESQUEMAS DE RESPONSE
# ====================================

class EvidenciaResponseSchema(BaseModel):
    """
    Respuesta de evidencia.
    """
    id_evidencia: int
    titulo: str
    tipo_formato: str
    ruta_archivo_pdf: str
    estado: str
    fecha_carga: datetime
    fecha_deadline: Optional[datetime]

    class Config:
        from_attributes = True
        example = {
            "id_evidencia": 1,
            "titulo": "Bitácora Semana 3",
            "tipo_formato": "Bitácora",
            "ruta_archivo_pdf": "/uploads/3388939/bitacora_semana3.pdf",
            "estado": "Pendiente",
            "fecha_carga": "2025-09-18T10:30:00",
            "fecha_deadline": "2025-10-15T23:59:59"
        }


class RetroalimentacionResponseSchema(BaseModel):
    """
    Respuesta de retroalimentación.
    """
    id_retroalimentacion: int
    id_evidencia: int
    id_instructor: int
    observaciones: str
    estado_evaluacion: str
    fecha_revision: datetime

    class Config:
        from_attributes = True
        example = {
            "id_retroalimentacion": 1,
            "id_evidencia": 1,
            "id_instructor": 2,
            "observaciones": "Buena bitácora, cumple con los requisitos.",
            "estado_evaluacion": "Aprobada",
            "fecha_revision": "2025-09-19T14:30:00"
        }


class AlertaVencimientoSchema(BaseModel):
    """
    Alerta de vencimiento de una evidencia pendiente (RNF seguimiento).

    Campos:
    - dias_restantes: negativo => ya venció
    - estado_alerta: "Vencida" | "Por vencer"
    """
    id_evidencia: int
    titulo: str
    fecha_deadline: datetime
    dias_restantes: int
    estado_alerta: str

    class Config:
        example = {
            "id_evidencia": 3,
            "titulo": "Bitácora Semana 4",
            "fecha_deadline": "2026-10-05T23:59:00",
            "dias_restantes": 2,
            "estado_alerta": "Por vencer",
        }


class RetroalimentacionCreateSchema(BaseModel):
    """Request para crear retroalimentación independiente (POST)."""
    id_evidencia: int
    observaciones: str = Field(..., min_length=10, max_length=1000)
    estado_evaluacion: Optional[str] = Field(
        None, pattern="^(Aprobada|Ajuste Requerido)$"
    )
