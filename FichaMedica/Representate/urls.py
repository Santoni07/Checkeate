from django.urls import path
from .views import RepresentanteHomeView,TraerEquiposPorCategorias,  colegio_home_view, RepresentanteActividadGeneralHomeView
from . import views

urlpatterns = [
   path('representante-home/', RepresentanteHomeView.as_view(), name='representante_home'),
   path('ajax/traer-equipos/',TraerEquiposPorCategorias.as_view(), name='traer_equipos'),
   path('colegio_home/', views.colegio_home_view, name='colegio_home'),
    path(
        'actividad-general-home/',
        RepresentanteActividadGeneralHomeView.as_view(),
        name='representante_actividad_general_home'
    ),
     path('estadisticas/', views.estadisticas_colegio, name='estadisticas_colegio'),
     path("ver-estudios-representante/", views.ver_estudios_representante, name="ver_estudios_representante"),



]