# app/models/refresh_token.py
"""
MODELO: RefreshToken - detección de reuso de refresh tokens.

EXPLICACIÓN: un JWT stateless no puede invalidarse; guardar el jti en BD
permite detectar reuso (posible robo) y matar la cadena de tokens.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.models.usuario import Base


class RefreshToken(Base):
    """Registro persistente de cada refresh token emitido."""

    __tablename__ = "refresh_tokens"

    id_token = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID del registro del token"
    )

    jti = Column(
        String(36),
        unique=True,
        nullable=False,
        comment="UUID del token (claim jti del JWT)"
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Dueño del token (borrar usuario => borrar sus tokens)"
    )

    emitido_en = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        comment="Cuándo se emitió el token"
    )

    expira_en = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Expiración (misma que el claim exp del JWT)"
    )

    usado = Column(
        Integer,
        default=0,
        comment="0=activo, 1=ya canjeado (reuso => ataque)"
    )
