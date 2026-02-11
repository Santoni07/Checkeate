from django.urls import path
from .views.me import mis_aptos, me_roles, seleccionar_rol
from .views.jugador_home import *
from .views.paciente_home import *
from ApiRest.views.aptos import detalle_apto_general
from ApiRest.views.registros_medicos import detalle_registro_medico
from .views.auth import api_login


urlpatterns = [
    path("login/", api_login),
    path("me/aptos/", mis_aptos, name="api_me_aptos"),
    path("me/roles/", me_roles, name="api_me_roles"),
    path("me/seleccionar_rol/", seleccionar_rol, name="api_seleccionar_rol"),
    
    path("aptos/general/<int:id>/", detalle_apto_general),
    path("registros-medicos/<int:id>/", detalle_registro_medico),
    path("jugador/home/", jugador_home),
    path("paciente/home/", paciente_home),

]