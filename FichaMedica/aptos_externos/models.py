from django.db import models
from django.core.exceptions import ValidationError

from persona.models import Persona
from account.models import Profile
from persona.models import Torneo, Competencia,ActividadGeneral



class AptoExterno(models.Model):

    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="aptos_externos"
    )

    representante = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="aptos_externos_cargados"
    )

    # 🔗 ASOCIACIÓN FUNCIONAL
    actividad = models.ForeignKey(
        ActividadGeneral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aptos_externos",
        help_text="Actividad general asociada al apto externo"
    )

    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aptos_externos",
        help_text="Torneo asociado al apto externo"
    )

    competencia = models.ForeignKey(
        Competencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aptos_externos",
        help_text="Competencia específica dentro del torneo"
    )

    # 📄 DOCUMENTO
    archivo_pdf = models.FileField(upload_to="aptos_externos/")

    # 📅 FECHAS
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()

    # 📝 CONTROL ADMINISTRATIVO
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones administrativas del apto externo"
    )

    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_emision"]
        verbose_name = "Apto Externo"
        verbose_name_plural = "Aptos Externos"

    def __str__(self):
        destino = self.actividad or self.competencia or self.torneo
        return f"Apto externo - {self.persona} ({destino})"

    # 🧠 VALIDACIÓN DE NEGOCIO
    def clean(self):
        """
        Regla:
        - No se puede asignar actividad y torneo al mismo tiempo
        - Competencia solo es válida si hay torneo
        """
        if self.actividad and self.torneo:
            raise ValidationError(
                "El apto externo no puede estar asociado a una actividad y a un torneo al mismo tiempo."
            )

        if self.competencia and not self.torneo:
            raise ValidationError(
                "La competencia solo puede asignarse si hay un torneo seleccionado."
            )
