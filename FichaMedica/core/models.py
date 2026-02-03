from django.db import models

# Create your models here.
from django.db import models
from django.utils.timezone import now

class EmailLog(models.Model):
    TIPO_CERTIFICADO = [
        ("apto", "Apto Físico General"),
        ("registro", "Registro Médico"),
        ("cus", "Certificado Único de Salud"),
        ("otro", "Otro"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CERTIFICADO, default="otro")
    destinatario = models.EmailField()
    asunto = models.CharField(max_length=255)
    cuerpo = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, default="PENDIENTE")
    respuesta_servidor = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.destinatario} ({self.asunto}) - {self.estado}"

    class Meta:
        db_table = "email_log"
        verbose_name = "Registro de Email"
        verbose_name_plural = "Registros de Emails"
        ordering = ["-fecha_envio"]