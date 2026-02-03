from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import AptoExterno


@admin.register(AptoExterno)
class AptoExternoAdmin(admin.ModelAdmin):

    # ================== LISTADO ==================
    list_display = (
        "persona_display",
        "destino_display",
        "fecha_emision",
        "fecha_vencimiento",
        "vigencia_display",
        "documento_link",
        "activo",
    )

    list_filter = (
        "activo",
        "fecha_emision",
        "fecha_vencimiento",
        "actividad",
        "torneo",
        "competencia",
        "representante",
    )

    search_fields = (
        "persona__profile__apellido",
        "persona__profile__nombre",
        "persona__profile__dni",
        "observaciones",
    )

    ordering = ("-fecha_emision",)

    # ================== EDICIÓN ==================
    readonly_fields = (
        "creado_en",
        "vigencia_display",
    )

    fieldsets = (
        ("Paciente", {
            "fields": ("persona",)
        }),
        ("Representante", {
            "fields": ("representante",)
        }),
        ("Asociación", {
            "description": "Asignar a una actividad general o a un torneo/competencia",
            "fields": ("actividad", "torneo", "competencia")
        }),
        ("Documento", {
            "fields": ("archivo_pdf",)
        }),
        ("Fechas", {
            "fields": ("fecha_emision", "fecha_vencimiento")
        }),
        ("Observaciones", {
            "fields": ("observaciones",)
        }),
        ("Estado", {
            "fields": ("activo", "vigencia_display", "creado_en")
        }),
    )

    # ================== MÉTODOS VISUALES ==================

    @admin.display(description="Paciente")
    def persona_display(self, obj):
        p = obj.persona.profile
        return f"{p.apellido}, {p.nombre} ({p.dni})"

    @admin.display(description="Destino")
    def destino_display(self, obj):
        if obj.actividad:
            return format_html("🏃 <strong>{}</strong>", obj.actividad)
        if obj.competencia:
            return format_html("🏆 <strong>{}</strong>", obj.competencia)
        if obj.torneo:
            return format_html("🏟️ <strong>{}</strong>", obj.torneo)
        return format_html("<span style='color:#999;'>— General —</span>")

    @admin.display(description="Vigencia")
    def vigencia_display(self, obj):
        hoy = timezone.now().date()
        if obj.fecha_vencimiento >= hoy:
            return format_html(
                "<span style='color:green;font-weight:bold;'>Vigente</span>"
            )
        return format_html(
            "<span style='color:red;font-weight:bold;'>Vencido</span>"
        )

    @admin.display(description="Documento")
    def documento_link(self, obj):
        if obj.archivo_pdf:
            return format_html(
                '<a href="{}" target="_blank" style="font-weight:bold;">📄 Ver PDF</a>',
                obj.archivo_pdf.url
            )
        return "-"

    # ================== SEGURIDAD BÁSICA ==================
    def has_delete_permission(self, request, obj=None):
        # Evita borrados accidentales
        return request.user.is_superuser