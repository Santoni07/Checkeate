from django.contrib import admin

# Register your models here.

from .models import *

@admin.register(Representante)
class RepresentanteAdmin(admin.ModelAdmin):
    list_display = ('profile', 'torneo')
    list_filter = ('profile', 'torneo')
    search_fields = ('profile__user__username', 'torneo__nombre')


@admin.register(RepresenteColegio)
class RepresenteColegioAdmin(admin.ModelAdmin):
    list_display = ('Profile', 'colegio')
    list_filter = ('Profile', 'colegio')

@admin.register(RepresentanteActividadGeneral)
class RepresentanteActividadGeneralAdmin(admin.ModelAdmin):
    list_display = ("id", "profile_nombre", "profile_apellido", "actividad")
    search_fields = ("profile__nombre", "profile__apellido", "profile__dni", "actividad__nombre")
    list_filter = ("actividad",)

    def profile_nombre(self, obj):
        return obj.profile.nombre
    profile_nombre.short_description = "Nombre"

    def profile_apellido(self, obj):
        return obj.profile.apellido
    profile_apellido.short_description = "Apellido"