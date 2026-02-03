from django.contrib import admin
from .models import Medico, Documentos, ObservacionPersona
from django.utils.html import format_html

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre_completo',
        'matricula',
        'especialidad',
        'telefono_consultorio',
        'direccion',  # ✅ Nuevo campo
        'mostrar_firma'
    )
    search_fields = (
        'profile__nombre',
        'profile__apellido',
        'matricula',
        'especialidad',
        'direccion'  # ✅ Para buscar por dirección también
    )
    list_filter = ('especialidad',)

    readonly_fields = ('mostrar_firma',)

    def nombre_completo(self, obj):
        return f"{obj.profile.nombre} {obj.profile.apellido}"
    nombre_completo.short_description = 'Nombre Completo'

    def mostrar_firma(self, obj):
        if obj.firma:
            return format_html('<img src="{}" width="100" height="40" style="object-fit:contain;"/>', obj.firma.url)
        return "Sin firma"
    mostrar_firma.short_description = "Firma"

@admin.register(Documentos)
class DocumentacionAdmin(admin.ModelAdmin):
    list_display = ['medico', 'fecha_carga', 'ver_matricula', 'estado_qr']
    readonly_fields = ['fecha_carga', 'ver_matricula']
    search_fields = ['medico__profile__nombre', 'medico__profile__apellido']

    def ver_matricula(self, obj):
        if obj.certificado_matricula:
            return format_html(
                '<a class="button" href="{}" target="_blank">Ver PDF</a>',
                obj.certificado_matricula.url
            )
        return "No cargado"
    ver_matricula.short_description = "Matrícula"

    def estado_qr(self, obj):
        return "Válido ✅" if obj.qr_valido else "Inválido ❌"



    estado_qr.short_description = "QR"


@admin.register(ObservacionPersona)
class ObservacionPersonaAdmin(admin.ModelAdmin):
    list_display = (
        "persona",
        "rol_autor",
        "autor_profile",
        "creado_en",
    )

    list_filter = (
        "rol_autor",
        "creado_en",
    )

    search_fields = (
        "persona__nombre",
        "persona__apellido",
        "observacion",
    )

    autocomplete_fields = (
        "persona",
        "autor_profile",
    )

    readonly_fields = (
        "creado_en",
    )

    ordering = (
        "-creado_en",
    )

    fieldsets = (
        ("Persona", {
            "fields": ("persona",),
        }),
        ("Autor", {
            "fields": ("rol_autor", "autor_profile"),
        }),
        ("Observación", {
            "fields": ("observacion",),
        }),
        ("Datos del sistema", {
            "fields": ("creado_en",),
        }),
    )