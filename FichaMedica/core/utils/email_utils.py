from django.core.mail import EmailMessage, get_connection
from django.conf import settings

def enviar_correo(asunto, cuerpo, destinatarios, remitente_key, tipo="otro"):
    """Envía un correo de texto plano y registra el resultado en EmailLog."""
    from core.models import EmailLog  # import interno evita ciclos

    if remitente_key not in settings.EMAIL_ACCOUNTS:
        raise ValueError("Cuenta de correo no configurada.")

    # 🔹 Limpieza y guard rails
    destinatarios = [d.strip() for d in destinatarios if d and d.strip()]
    if not destinatarios:
        EmailLog.objects.create(
            tipo=tipo, destinatario="", asunto=asunto,
            estado="ERROR", respuesta_servidor="Destinatario vacío o inválido"
        )
        return

    cuenta = settings.EMAIL_ACCOUNTS[remitente_key]

    connection = get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=cuenta['EMAIL_HOST_USER'],
        password=cuenta['EMAIL_HOST_PASSWORD'],
        use_tls=settings.EMAIL_USE_TLS,
    )

    email = EmailMessage(
        subject=asunto,
        body=cuerpo,
        from_email=cuenta['EMAIL_HOST_USER'],  # 👈 debe coincidir con la cuenta autenticada
        to=destinatarios,
        connection=connection
    )

    estado = "PENDIENTE"
    respuesta = ""

    try:
        email.send()
        estado = "ENVIADO"
        respuesta = "OK"
    except Exception as e:
        respuesta = str(e)
        estado = "RECHAZADO" if "550 5.1.1" in respuesta else "ERROR"

    EmailLog.objects.create(
        tipo=tipo,
        destinatario=",".join(destinatarios),
        asunto=asunto,
        estado=estado,
        respuesta_servidor=respuesta,
    )

