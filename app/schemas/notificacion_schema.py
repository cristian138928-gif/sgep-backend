# app/schemas/notificacion_schema.py
"""
Esquemas Pydantic para notificaciones in-app.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificacionResponseSchema(BaseModel):
    """Notificación dirigida a un usuario autenticado."""
    id_notificacion: int
    mensaje: str
    tipo: str  # evaluacion | vencimiento | sistema
    id_evidencia: int | None
    leida: bool  # EXPLICACIÓN: 0/1 de BD expuesto como bool en la API
    fecha_creacion: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id_notificacion": 1,
            "mensaje": "Tu evidencia 'Bitácora Semana 3' fue Aprobada",
            "tipo": "evaluacion",
            "id_evidencia": 7,
            "leida": False,
            "fecha_creacion": "2026-10-04T10:30:00"
        }},
    )


class ConteoNoLeidasSchema(BaseModel):
    """Badge de notificaciones sin leer."""
    no_leidas: int
