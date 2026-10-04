# tests/test_email.py
"""
Tests del servicio de email (etapa B2).
Cubre: modo consola, envío SMTP con backend falso, asunto de evaluación.
"""

import logging

from app.config import settings
from app.services import email_service


def test_email_desactivado_solo_log(monkeypatch, caplog):
    """EMAIL_ACTIVO=false => no toca SMTP, solo escribe en el log."""
    monkeypatch.setattr(settings, "email_activo", False)

    with caplog.at_level(logging.INFO, logger="sgep.email"):
        email_service.enviar_email("Asunto", "dest@test.com", "cuerpo")

    assert "consola" in caplog.text
    assert "dest@test.com" in caplog.text


def test_email_smtp_construye_mensaje(monkeypatch):
    """EMAIL_ACTIVO=true => el mensaje llega con To/Subject/From correctos."""
    capturas: dict = {}

    class FakeSMTP:
        """EXPLICACIÓN: Backend falso para no depender de un servidor SMTP."""

        def __init__(self, host, port, timeout=None):
            capturas["host"] = host
            capturas["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def send_message(self, mensaje):
            capturas["mensaje"] = mensaje

    monkeypatch.setattr(settings, "email_activo", True)
    monkeypatch.setattr(settings, "email_user", "")  # sin login => sin TLS
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    email_service.enviar_email("Asunto de prueba", "dest@test.com", "Hola")

    assert capturas["mensaje"]["To"] == "dest@test.com"
    assert capturas["mensaje"]["Subject"] == "Asunto de prueba"
    assert capturas["mensaje"]["From"] == settings.email_from


def test_email_evaluacion_usa_estado_en_asunto(monkeypatch):
    """El callback de evaluación refleja estado y título en el asunto."""
    capturas: dict = {}
    monkeypatch.setattr(
        email_service,
        "enviar_email",
        lambda asunto, destino, cuerpo: capturas.update(
            asunto=asunto, destino=destino, cuerpo=cuerpo
        ),
    )

    email_service.email_evaluacion(
        "aprendiz@test.com", "Bitacora 3", "Ajuste Requerido", "Falta firma"
    )

    assert "Ajuste Requerido" in capturas["asunto"]
    assert "Bitacora 3" in capturas["asunto"]
    assert capturas["destino"] == "aprendiz@test.com"
    assert "Falta firma" in capturas["cuerpo"]
