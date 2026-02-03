from django.urls import path
from . import views
from .views import medicos_inscriptos_view


urlpatterns = [
    path('registrar/', views.registrar_persona, name='registrar_persona'),  # URL para registrar persona
    #path('seleccionar_torneo_categoria/', seleccionar_torneo_categoria, name='seleccionar_torneo_categoria'),
   # URL para la vista del jugador
    path('rerror_registro/', views.error_registro, name='rerror_registro'),
    path('seleccionar_categoria_equipo/', views.seleccionar_categoria_equipo, name='seleccionar_categoria_equipo'),
    path('fetch_categorias/<int:torneo_id>/', views.fetch_categorias, name='fetch_categorias'),
    path('fetch_equipos/<int:categoria_id>/', views.fetch_equipos, name='fetch_equipos'),
    path('menu_jugador/', views.menu_jugador, name='menu_jugador'),
    path('perfil/', views.perfil, name='perfil'),
     # URL para cambiar el email
    path('modificar_email/', views.cambiar_email, name='modificar_email'),
    # URL para menu_aptosGenerales
    path("menu_paciente/", views.menu_paciente, name="menu_paciente"),
    # URL para cambiar la contraseña
    path('modificar_contrasena/', views.cambiar_contraseña, name='modificar_contrasena'),
    path('medicos/', medicos_inscriptos_view, name='medicos_inscriptos'),
    path("eventos/", views.listado_eventos_view, name="listado_eventos"),



    path('modificar_perfil/', views.modificar_perfil, name='modificar_perfil'),

    # URL para inscribirse en un nuevo torneo
    path('inscribirse-a-torneo/', views.inscribirse_a_torneo, name='inscribirse_a_torneo'),
    path("actividad/<int:actividad_id>/inscribirse/", views.inscribirse_actividad, name="inscribirse_actividad"),
    path("inscribirse_actividad/", views.inscribirse_actividad_view, name="inscribirse_actividad_view"),

]
"""
 path('seleccionar_torneo/', seleccionar_torneo, name='seleccionar_torneo'),
    path('selecciona_categoria_y_equipo/', seleccionar_categoria_equipo, name='selecciona_categoria_equipo'), """