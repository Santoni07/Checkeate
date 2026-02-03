from django.contrib import admin
from .models import Persona, Jugador, Torneo, Categoria, Equipo, CategoriaEquipo, JugadorCategoriaEquipo, Competencia, JugadorCompetencia,ActividadGeneral, JugadorActividadGeneral

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'direccion', 'telefono', 'telefono_alternativo')
    search_fields = ('profile__nombre', 'profile__apellido')

@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('persona_nombre', 'grupo_sanguineo', 'cobertura_medica', 'numero_afiliado')
    search_fields = ('persona__profile__nombre', 'persona__profile__apellido')

    def persona_nombre(self, obj):
        return f"{obj.persona.profile.nombre} {obj.persona.profile.apellido}"
    persona_nombre.short_description = 'Nombre del Jugador'

@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'imagen')
    search_fields = ('nombre',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'torneo')
    search_fields = ('nombre',)

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(CategoriaEquipo)
class CategoriaEquipoAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'equipo')
    search_fields = ('categoria__nombre', 'equipo__nombre')

@admin.register(JugadorCategoriaEquipo)
class JugadorCategoriaEquipoAdmin(admin.ModelAdmin):
    list_display = ('get_id_jugador', 'get_nombre_completo_jugador', 'categoria_equipo')
    search_fields = ('jugador__persona__profile__nombre', 'jugador__persona__profile__apellido')
    list_filter = ('categoria_equipo__categoria', 'categoria_equipo__equipo')

    # Mostrar ID del jugador
    def get_id_jugador(self, obj):
        return obj.jugador.id
    get_id_jugador.short_description = 'ID Jugador'
    get_id_jugador.admin_order_field = 'jugador__id'

    # Mostrar nombre completo
    def get_nombre_completo_jugador(self, obj):
        return f"{obj.jugador.persona.profile.nombre} {obj.jugador.persona.profile.apellido}"
    get_nombre_completo_jugador.short_description = 'Jugador'
    get_nombre_completo_jugador.admin_order_field = 'jugador__persona__profile__nombre'


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'direccion', 'telefono', 'activo')
    search_fields = ('nombre', 'descripcion', 'direccion', 'telefono')
    list_filter = ('activo',)
    ordering = ('nombre',)

@admin.register(JugadorCompetencia)
class JugadorCompetenciaAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'competencia')
    search_fields = ('jugador__persona__nombre', 'jugador__persona__apellido', 'competencia__nombre')
    list_filter = ('competencia',)
    ordering = ('competencia',)

@admin.register(ActividadGeneral)
class ActividadGeneralAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "direccion", "telefono", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion", "direccion", "telefono")
    ordering = ("nombre",)


@admin.register(JugadorActividadGeneral)
class JugadorActividadGeneralAdmin(admin.ModelAdmin):
    list_display = ("jugador", "actividad")
    list_filter = ("actividad",)
    search_fields = ("jugador__persona__profile__apellido", "jugador__persona__profile__nombre", "actividad__nombre")
    ordering = ("actividad", "jugador")
