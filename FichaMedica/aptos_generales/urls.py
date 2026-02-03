from django.urls import path
from . import views

app_name = "aptos_generales"

urlpatterns = [
    path("antecedentes/", views.antecedentes_home, name="antecedentes_home"),
    path("apto/<int:apto_id>/antecedentes/detail/", views.antecedentes_detail, name="antecedentes_detail"),
    path("apto/<int:apto_id>/antecedentes/", views.antecedentes_list, name="antecedentes_list"),
    path("apto/<int:apto_id>/antecedentes/create/", views.antecedentes_create, name="antecedentes_create"),
    path("apto/<int:apto_id>/antecedentes/update/", views.antecedentes_update, name="antecedentes_update"),
    path("apto/<int:apto_id>/antecedentes/delete/", views.antecedentes_delete, name="antecedentes_delete"),
    path("antecedentes/select/", views.antecedentes_select, name="antecedentes_select"),
    path("estudios/", views.ver_estudios_jugador, name="ver_estudios_jugador"),



]
