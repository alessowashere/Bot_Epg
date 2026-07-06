import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def _smtp_config():
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASSWORD"),
        "from": os.getenv("SMTP_FROM") or os.getenv("SMTP_USER"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() != "false",
    }


def enviar_correo(destinatario, asunto, cuerpo_html, adjuntos=None):
    adjuntos = adjuntos or []
    cfg = _smtp_config()
    if not cfg["host"] or not cfg["from"]:
        raise RuntimeError("Configura SMTP_HOST y SMTP_FROM/SMTP_USER para enviar correos")

    mensaje = MIMEMultipart()
    mensaje["From"] = cfg["from"]
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    for ruta in adjuntos:
        path = Path(ruta)
        if not path.exists():
            continue
        parte = MIMEApplication(path.read_bytes(), Name=path.name)
        parte["Content-Disposition"] = f'attachment; filename="{path.name}"'
        mensaje.attach(parte)

    with smtplib.SMTP(cfg["host"], cfg["port"]) as smtp:
        if cfg["use_tls"]:
            smtp.starttls()
        if cfg["user"] and cfg["password"]:
            smtp.login(cfg["user"], cfg["password"])
        smtp.send_message(mensaje)

    return {"status": "enviado", "destinatario": destinatario}


def notificar_dictaminante(docente, expediente):
    asunto = f"Asignacion como dictaminante - Expediente {expediente.codigo_alumno}"
    
    asig = next((a for a in expediente.asignaciones if a.id_docente == docente.id_docente and a.rol_asignado == "Dictaminante"), None)
    uuid_str = asig.uuid if asig else ""
    frontend_url = os.getenv("FRONTEND_URL", "https://tusistema.com")

    cuerpo = f"""
    <p>Estimado/a {docente.nombre_completo},</p>
    <p>Ha sido asignado/a como dictaminante del expediente de tesis de
    <strong>{expediente.nombre_alumno}</strong>.</p>
    <p><strong>Titulo:</strong> {expediente.titulo_tesis or 'No registrado'}</p>
    <p>Ingrese al siguiente enlace seguro para aceptar o declinar la asignacion:</p>
    <p><a href="{frontend_url}/#/dictaminante/{uuid_str}">Responder a la Asignacion</a></p>
    """
    return enviar_correo(docente.correo, asunto, cuerpo) if getattr(docente, "correo", None) else None


def notificar_alumno_via_bot(ticket_id, mensaje, archivo_resolucion=None):
    from sincronizador import responder_ticket

    return responder_ticket(ticket_id, mensaje, archivo_resolucion)
