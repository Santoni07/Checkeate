from django.urls import path
from .views.me import mis_aptos, me_roles, seleccionar_rol, me_overview
from .views.jugador_home import *
from .views.paciente_home import *
from ApiRest.views.aptos import detalle_apto_general,mis_aptos_general
from ApiRest.views.registros_medicos import *
from .views.auth import api_login
from .views.register import verificar_email
from .views.onboarding import seleccionar_servicio
from .views.auth import register
from .views.jugador import mis_registros_medicos
from .views.apto_general import *

urlpatterns = [
    path("login/", api_login),
    path("register/", register),
    path("register/verificar-email/", verificar_email),
    path("seleccionar-servicio/", seleccionar_servicio),
    path('api/me/', me_overview, name='me_overview'),
    path("me/aptos/", mis_aptos, name="api_me_aptos"),
    path("me/roles/", me_roles, name="api_me_roles"),
    path("me/seleccionar_rol/", seleccionar_rol, name="api_seleccionar_rol"),
    
    path("aptos/general/<int:id>/", detalle_apto_general),
    path("registros-medicos/<int:id>/", detalle_registro_medico),
    path("jugador/registros/", mis_registros_medicos),
    path(
    "registros-medicos/<int:id>/pdf/",
    descargar_pdf_registro,
    name="api_descargar_pdf_registro"
),
    path("aptos/mis-aptos/", mis_aptos_general),
    path("jugador/home/", jugador_home),
    path("paciente/home/", paciente_home),
    
    # 📋 LISTA DE APTOS DEL USUARIO LOGUEADO
    path(
        "aptos/general/",
        mis_aptos_general,
        name="mis_aptos_general"
    ),

    # 🔎 DETALLE COMPLETO DEL APTO
    path(
        "aptos/general/<int:id>/",
        detalle_apto_general_mobile,
        name="detalle_apto_general_mobile"
    ),
    path(
    "aptos/general/<int:id>/pdf/",
    descargar_pdf_apto_general,
    name="api_descargar_pdf_apto_general"
),
    #Descargar estudios medicos para RegistrosMedicos
    path(
    "registros-medicos/estudios/<int:id>/pdf/",
    descargar_estudio_registro,
    name="api_descargar_estudio_registro"
),
    path(
    "jugador/estudios/",
    mis_estudios_registro,
    name="mis_estudios_registro"
),
   
    path("paciente/estudios-apto/", paciente_estudios_apto),
    
    path(
    "aptos/estudios/<int:id>/pdf/",
    descargar_pdf_estudio_apto,
    name="api_descargar_estudio_apto"
),
]