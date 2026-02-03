
from django.urls import path
from .views import torneos_adheridos, actividades_generales_adheridas



urlpatterns = [
    path("api/torneos-adheridos/", torneos_adheridos, name="api_torneos_adheridos"),
    path("api/actividades-adheridas/", actividades_generales_adheridas, name="api_actividades_adheridas"),

]