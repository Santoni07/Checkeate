from django.db import models
from django.utils import timezone
from datetime import date
from Medico.models import Medico
from persona.models import Jugador, ActividadGeneral

try:
    from antecedentes.models import AntecedenteEnfermedades  # ajustar si cambia
except Exception:
    AntecedenteEnfermedades = None

try:
    # Preciso para “1 año” real (maneja bisiestos, meses)
    from dateutil.relativedelta import relativedelta
except ImportError:
    relativedelta = None
from datetime import timedelta

def caduca_en_un_ano():
    hoy = timezone.now().date()
    if relativedelta:
        return hoy + relativedelta(years=1)
    return hoy + timedelta(days=365)  # fallback si no tenés dateutil

class AptoGeneral(models.Model):
    ESTADO_FICHA = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESO', 'En proceso'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('VENCIDO', 'Vencido'),
    ]
    actividad = models.ForeignKey(
        ActividadGeneral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aptos"
    )
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='aptos_generales')

    estado = models.CharField(max_length=45, choices=ESTADO_FICHA, blank=True, null=True, default='PROCESO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_caducidad = models.DateField(blank=True, null=True)
    fecha_de_llenado = models.DateField(blank=True, null=True)
    observacion = models.CharField(max_length=200, blank=True, null=True)
    consentimiento_persona = models.BooleanField(null=True, blank=True)
    medico = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        if self.jugador and self.jugador.persona and self.jugador.persona.user:
            u = self.jugador.persona.user
            return f"AptoGeneral #{self.id} - {u.last_name}, {u.first_name} - {self.estado}"

        return f"AptoGeneral #{self.id} - {self.estado}"


class AntecedenteAptoGeneral(models.Model):
    """
    Snapshot de antecedentes para UN Apto General.
    Cada jugador puede tener varios (uno por AptoGeneral).
    """
    apto = models.OneToOneField(AptoGeneral, on_delete=models.CASCADE, related_name='antecedentes_snapshot')
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='antecedentes_por_apto')
    creado_en = models.DateTimeField(auto_now_add=True)

    # --- CAMPOS ---
    fue_operado = models.BooleanField(null=True, blank=True, default=None)
    toma_medicacion = models.BooleanField(null=True, blank=True, default=None)
    estuvo_internado = models.BooleanField(null=True, blank=True, default=None)
    sufre_hormigueos = models.BooleanField(null=True, blank=True, default=None)
    es_diabetico = models.BooleanField(null=True, blank=True, default=None)
    es_asmatico = models.BooleanField(null=True, blank=True, default=None)
    es_alergico = models.BooleanField(null=True, blank=True, default=None)
    alerg_observ = models.CharField(max_length=100, null=True, blank=True, default=None)
    antecedente_epilepsia = models.BooleanField(null=True, blank=True, default=None)
    desviacion_columna = models.BooleanField(null=True, blank=True, default=None)
    dolor_cintura = models.BooleanField(null=True, blank=True, default=None)
    fracturas = models.BooleanField(null=True, blank=True, default=None)
    dolores_articulares = models.BooleanField(null=True, blank=True, default=None)
    falta_aire = models.BooleanField(null=True, blank=True, default=None)
    traumatismos_craneo = models.BooleanField(null=True, blank=True, default=None)
    dolor_pecho = models.BooleanField(null=True, blank=True, default=None)
    perdida_conocimiento = models.BooleanField(null=True, blank=True, default=None)
    presion_arterial = models.BooleanField(null=True, blank=True, default=None)
    muerte_subita_familiar = models.BooleanField(null=True, blank=True, default=None)
    enfermedad_cardiaca_familiar = models.BooleanField(null=True, blank=True, default=None)
    soplo_cardiaco = models.BooleanField(null=True, blank=True, default=None)
    abstenerse_competencia = models.BooleanField(null=True, blank=True, default=None)
    antecedentes_coronarios_familiares = models.BooleanField(null=True, blank=True, default=None)
    fumar_hipertension_diabetes = models.BooleanField(null=True, blank=True, default=None)
    fhd_observacion = models.CharField(max_length=100, null=True, blank=True, default=None)
    consumo_cocaina_anabolicos = models.BooleanField(null=True, blank=True, default=None)
    cca_observaciones = models.CharField(max_length=100, null=True, blank=True, default=None)

    vacunacion = models.BooleanField(null=True, blank=True, default=None)

    class Meta:
        ordering = ['-creado_en']
        constraints = [
            models.UniqueConstraint(fields=['apto'], name='uniq_antecedente_por_apto'),
        ]

    def esta_completo(self):
        """
        Devuelve True si al menos un campo fue contestado (True, False o texto).
        Devuelve False si TODOS están en None (vacío).
        """
        campos = [
            self.fue_operado,
            self.toma_medicacion,
            self.estuvo_internado,
            self.sufre_hormigueos,
            self.es_diabetico,
            self.es_asmatico,
            self.es_alergico,
            self.alerg_observ,
            self.antecedente_epilepsia,
            self.desviacion_columna,
            self.dolor_cintura,
            self.fracturas,
            self.dolores_articulares,
            self.falta_aire,
            self.traumatismos_craneo,
            self.dolor_pecho,
            self.perdida_conocimiento,
            self.presion_arterial,
            self.muerte_subita_familiar,
            self.enfermedad_cardiaca_familiar,
            self.soplo_cardiaco,
            self.abstenerse_competencia,
            self.antecedentes_coronarios_familiares,
            self.fumar_hipertension_diabetes,
            self.fhd_observacion,
            self.consumo_cocaina_anabolicos,
            self.cca_observaciones,
            self.vacunacion,
        ]

        return any(campo is not None for campo in campos)

    def __str__(self):
        try:
            persona = self.apto.jugador.persona
            profile = persona.profile if persona else None

            if profile:
                return f"Antecedentes (Apto {self.apto_id}) de {profile.nombre} {profile.apellido}"
            else:
                return f"Antecedentes (Apto {self.apto_id}) – Persona sin perfil"
        except Exception:
            return f"Antecedentes (Apto {self.apto_id})"


# Examen fisico General
class ExamenFisicoGeneral(models.Model):
    DIAGNOSTICO_ANTROPOMETRICO = [
        ('EUTROFICO', 'Eutrófico'),
        ('ENDOMORFO', 'Endomorfo'),
        ('MESOMORFO', 'Mesomorfo'),
        ('ECTOMORFO', 'Ectomorfo'),
    ]

    apto = models.OneToOneField(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="examen_fisico"
    )
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # kg
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)  # mts
    imc = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    perimetro_cintura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # 🔽 Select con opciones predefinidas
    diagnostico = models.CharField(
        max_length=20,
        choices=DIAGNOSTICO_ANTROPOMETRICO,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["apto"]

    def save(self, *args, **kwargs):
        if self.peso and self.altura:
            try:
                self.imc = round(self.peso / (self.altura ** 2), 2)
            except ZeroDivisionError:
                self.imc = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Examen físico Apto {self.apto_id}"

# Examen Cardiovascular

class ExamenCardiovascularGeneral(models.Model):
    apto = models.OneToOneField(AptoGeneral, on_delete=models.CASCADE, related_name="examen_cardiovascular")
    auscultacion = models.TextField(null=True, blank=True)
    ta1 = models.CharField(max_length=10, null=True, blank=True, help_text="Tensión arterial 1")
    ta2 = models.CharField(max_length=10, null=True, blank=True, help_text="Tensión arterial 2")
    pulso = models.CharField(max_length=50, null=True, blank=True)
    ecg = models.FileField(upload_to="ecg/", null=True, blank=True)  # opcional subir estudio

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Cardiovascular Apto {self.apto_id}"

# Examen Respiratorio

class ExamenRespiratorioGeneral(models.Model):
    apto = models.OneToOneField(AptoGeneral, on_delete=models.CASCADE, related_name="examen_respiratorio")
    murmullo_vesicular = models.CharField(max_length=100, null=True, blank=True)
    ruidos_agregados = models.CharField(max_length=100, null=True, blank=True)
    saturacion_o2 = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Respiratorio Apto {self.apto_id}"

# Examen de Abdomen
class ExamenAbdomenGeneral(models.Model):
    apto = models.OneToOneField(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="examen_abdomen"
    )
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Examen abdomen Apto {self.apto_id}"


# Examen Genitourinario General

class ExamenGenitourinarioGeneral(models.Model):
    apto = models.OneToOneField(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="examen_genitourinario"
    )
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Examen genitourinario Apto {self.apto_id}"

# Examen Soma General

class ExamenSomaGeneral(models.Model):
    apto = models.OneToOneField(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="examen_soma"
    )
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Examen soma Apto {self.apto_id}"

#  Motivo Actividad General

class MotivoActividadGeneral(models.Model):
    apto = models.OneToOneField(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="motivo_actividad"
    )

    competitivo = models.BooleanField(default=False)
    recreativo = models.BooleanField(default=False)

    # Salud o enfermedad
    por_salud = models.BooleanField(default=False)
    salud_detalle = models.CharField(max_length=200, null=True, blank=True)

    # Lesión
    por_lesion = models.BooleanField(default=False)
    lesion_detalle = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["apto"]

    def __str__(self):
        return f"Motivo actividad Apto {self.apto_id}"




def default_fecha_caducidad():
    hoy = timezone.now().date()
    if relativedelta:
        return hoy + relativedelta(years=1)
    return hoy + timedelta(days=365)

class EstudiosAptoGeneral(models.Model):
    TIPO_ESTUDIO = [
        ('ORINA', 'Análisis de Orina'),
        ('ELECTRO', 'Electrocardiograma'),
        ('ERGOMETRIA', 'Ergometría'),
        ('LABORATORIO', 'Laboratorio'),
        ('IMAGEN', 'Estudio por Imágenes'),
        ('OTRO', 'Otro'),
    ]

    idestudio = models.AutoField(primary_key=True)
    apto = models.ForeignKey(
        AptoGeneral,
        on_delete=models.CASCADE,
        related_name="estudios_apto"
    )
    tipo_estudio = models.CharField(max_length=20, choices=TIPO_ESTUDIO)
    archivo = models.FileField(upload_to='estudios_apto/', null=True, blank=True)
    observaciones = models.CharField(max_length=200, null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
    fecha_caducidad = models.DateField(default=default_fecha_caducidad)

    class Meta:
        db_table = 'estudios_apto_generales'
        verbose_name = 'Estudio Apto General'
        verbose_name_plural = 'Estudios Aptos Generales'
        ordering = ['-fecha_creacion']

    def save(self, *args, **kwargs):
        # Siempre fijar fecha_caducidad al 31 de diciembre del año de creación
        if self.fecha_creacion:
            year = self.fecha_creacion.year
        else:
            from django.utils import timezone
            year = timezone.now().year
        self.fecha_caducidad = date(year, 12, 31)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_estudio_display()} - Apto {self.apto.id}"
