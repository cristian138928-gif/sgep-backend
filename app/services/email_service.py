# app/services/email_service.py
"""
Envío de emails con backend conmutable (consola / SMTP).

EXPLICACIÓN: EMAIL_ACTIVO=false => solo log (dev/tests sin servidor SMTP);
EMAIL_ACTIVO=true => smtplib real. La función es sync a propósito:
se ejecuta con BackgroundTasks (threadpool), sin bloquear el event loop.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("sgep.email")


def enviar_email(asunto: str, destinatario: str, cuerpo: str) -> None:
    """
    Envía un email transaccional.

    Args:
        asunto: Asunto del mensaje
        destinatario: Email del destinatario
        cuerpo: Contenido en texto plano

    Raises:
        smtplib.SMTPException: Solo si EMAIL_ACTIVO=true y el envío falla
    """
    if not settings.email_activo:
        # EXPLICACIÓN: Modo consola para no romper dev/tests sin SMTP
        logger.info("[EMAIL->consola] para=%s asunto=%s", destinatario, asunto)
        return

    mensaje = EmailMessage()
    mensaje["From"] = settings.email_from
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    with smtplib.SMTP(settings.email_host, settings.email_port, timeout=10) as servidor:
        if settings.email_user:
            servidor.starttls()
            servidor.login(settings.email_user, settings.email_pass)
        servidor.send_message(mensaje)
    logger.info("[EMAIL->smtp] para=%s asunto=%s", destinatario, asunto)


def email_evaluacion(
    destinatario: str, titulo: str, estado: str, observaciones: str
) -> None:
    """Callback para BackgroundTasks: notifica la evaluación de una evidencia."""
    asunto = f"[SGEP] Evidencia {estado}: {titulo}"
    cuerpo = (
        f"Tu evidencia '{titulo}' fue evaluada.\n\n"
        f"Estado: {estado}\n"
        f"Observaciones: {observaciones}\n\n"
        "Ingresa a SGEP para ver los detalles."
    )
    enviar_email(asunto, destinatario, cuerpo)
