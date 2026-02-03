from django.db import models
from account.models import Profile
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode
import requests
import os
from django.utils import timezone
from persona.models import Persona

class Medico(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="medico")

    matricula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    telefono_consultorio = models.CharField(max_length=15, blank=True, null=True)
    firma = models.ImageField(upload_to='firmas/', null=True, blank=True)

    class Meta:
        db_table = 'medico'
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"

    def __str__(self):
        return f"Dr./Dra. {self.profile.nombre} {self.profile.apellido} - {self.especialidad}"

# Modelo para la documentacion del medico


def upload_to_matricula(instance, filename):
    return f"documentacion/medico_{instance.medico.id}/matricula/{filename}"

def upload_to_firma(instance, filename):
    return f"documentacion/medico_{instance.medico.id}/firma/{filename}"

class Documentos(models.Model):
    medico = models.OneToOneField(Medico, on_delete=models.CASCADE, related_name="documentacion")
    certificado_matricula = models.FileField(upload_to=upload_to_matricula, blank=True, null=True)
    certificado_firma_electronica = models.FileField(upload_to=upload_to_firma, blank=True, null=True)
    url_certificado = models.URLField(blank=True, null=True)
    qr_valido = models.BooleanField(default=False)
    contrato_aceptado = models.BooleanField(default=False)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Primero guarda para asegurar que el archivo esté disponible
        if self.certificado_matricula:
            resultado = self.procesar_qr_certificado()
            if resultado:
                self.url_certificado = resultado.get("url")
                self.qr_valido = resultado.get("valido", False)
                super().save(update_fields=["url_certificado", "qr_valido"])  # Guardar sin crear bucles

    def procesar_qr_certificado(self):
        try:
            ruta_pdf = self.certificado_matricula.path
            doc = fitz.open(ruta_pdf)
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                qrs = decode(img)
                for qr in qrs:
                    data = qr.data.decode("utf-8")
                    try:
                        response = requests.head(data, timeout=5)
                        if response.status_code == 200:
                            return {"valido": True, "url": data}
                    except requests.RequestException:
                        return {"valido": False, "url": data}
            return None
        except Exception as e:
            print(f"Error al procesar el QR: {e}")
            return None


class ObservacionPersona(models.Model):
    ROL_AUTOR_CHOICES = (
        ("MEDICO", "Médico"),
        ("REPRESENTANTE", "Representante"),
    )

    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="observaciones"
    )

    autor_profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rol_autor = models.CharField(
        max_length=20,
        choices=ROL_AUTOR_CHOICES
    )

    observacion = models.TextField()

    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.persona} - {self.rol_autor}"