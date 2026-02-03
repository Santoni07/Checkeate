from django.urls import path
from .views import cargar_apto_externo, listado_aptos_externos_por_actividad

urlpatterns = [
    path("cargar/", cargar_apto_externo, name="aptos_externos_cargar"),

    path(
        "actividad/",
        listado_aptos_externos_por_actividad,
        name="aptos_externos_listado_actividad"
    ),
]
