from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

def get_info_connection():
    return EmailBackend(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_ACCOUNTS['soporte']['EMAIL_HOST_USER'],
        password=settings.EMAIL_ACCOUNTS['soporte']['EMAIL_HOST_PASSWORD'],
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL,
        fail_silently=False
    )