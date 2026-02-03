# aptos_generales/admin.py
from django.contrib import admin
from .models import (
    AptoGeneral,
    AntecedenteAptoGeneral,
    ExamenFisicoGeneral,
    ExamenCardiovascularGeneral,
    ExamenRespiratorioGeneral,
    ExamenAbdomenGeneral,
    ExamenGenitourinarioGeneral,
    ExamenSomaGeneral,
    MotivoActividadGeneral,
    EstudiosAptoGeneral,
)

# ==============================
# Apto General
# ==============================

@admin.register(AptoGeneral)
class AptoGeneralAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "jugador",
        "actividad",
        "estado",
        "fecha_creacion",
        "fecha_caducidad",
        "medico",
    )
    list_filter = (
        "estado",
        "fecha_creacion",
        "fecha_caducidad",
        "actividad",
    )
    search_fields = (
        "jugador__persona__profile__nombre",
        "jugador__persona__profile__apellido",
        "actividad__nombre",
    )
    date_hierarchy = "fecha_creacion"
    ordering = ("-fecha_creacion",)


# ==============================
# Antecedentes
# ==============================
@admin.register(AntecedenteAptoGeneral)
class AntecedenteAptoGeneralAdmin(admin.ModelAdmin):
    list_display = ("id", "apto", "jugador", "creado_en", "es_diabetico", "es_asmatico", "es_alergico", "vacunacion")
    list_filter = ("es_diabetico", "es_asmatico", "es_alergico", "vacunacion")
    search_fields = ("jugador__persona__profile__apellido", "jugador__persona__profile__nombre")


# ==============================
# Examenes
# ==============================
@admin.register(ExamenFisicoGeneral)
class ExamenFisicoGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "peso", "altura", "imc", "perimetro_cintura", "diagnostico")
    list_filter = ("diagnostico",)
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(ExamenCardiovascularGeneral)
class ExamenCardiovascularGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "auscultacion", "ta1", "ta2", "pulso")
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(ExamenRespiratorioGeneral)
class ExamenRespiratorioGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "murmullo_vesicular", "ruidos_agregados", "saturacion_o2")
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(ExamenAbdomenGeneral)
class ExamenAbdomenGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "observacion")
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(ExamenGenitourinarioGeneral)
class ExamenGenitourinarioGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "observacion")
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(ExamenSomaGeneral)
class ExamenSomaGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "observacion")
    search_fields = ("apto__jugador__persona__profile__apellido",)


# ==============================
# Motivo Actividad
# ==============================
@admin.register(MotivoActividadGeneral)
class MotivoActividadGeneralAdmin(admin.ModelAdmin):
    list_display = ("apto", "competitivo", "recreativo", "por_salud", "salud_detalle", "por_lesion", "lesion_detalle")
    list_filter = ("competitivo", "recreativo", "por_salud", "por_lesion")
    search_fields = ("apto__jugador__persona__profile__apellido",)


@admin.register(EstudiosAptoGeneral)
class EstudiosAptoGeneralAdmin(admin.ModelAdmin):
    list_display = (
        "idestudio",
        "apto",
        "tipo_estudio",
        "observaciones",
        "fecha_creacion",
        "fecha_caducidad",
        "archivo_link",
    )
    list_filter = ("tipo_estudio", "fecha_creacion", "fecha_caducidad")
    search_fields = (
        "idestudio",
        "apto__id",
        "apto__jugador__persona__profile__apellido",
        "apto__jugador__persona__profile__nombre",
        "observaciones",
    )
    ordering = ("-fecha_creacion",)

    # Método para mostrar link de descarga si hay archivo
    def archivo_link(self, obj):
        if obj.archivo:
            return f"<a href='{obj.archivo.url}' target='_blank'>Ver archivo</a>"
        return "—"
    archivo_link.allow_tags = True
    archivo_link.short_description = "Archivo"


