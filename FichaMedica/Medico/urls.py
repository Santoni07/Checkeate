from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('medico_home/', MedicoHomeView.as_view(), name='medico_home'),
     # Ruta para el formulario Electro Basal

    # Ruta para el formulario de Registo medico
    path('registro_medico_update/<int:registro_id>/', views.registro_medico_update_view, name='registro_medico_update_view'),
    path('medico/electro_basal/<int:jugador_id>/<int:registro_id>/', views.electro_basal_view, name='electro_basal_view'),
    path('medico/electro_esfuerzo/<int:jugador_id>/<int:registro_id>/', views.electro_esfuerzo_view, name='electro_esfuerzo_view'),
    path('medico/otros_examenes_clinicos/<int:jugador_id>/<int:registro_id>/', views.otros_examenes_clinicos_view, name='otros_examenes_clinicos_view'),
    path('medico/cardiovascular/<int:jugador_id>/<int:registro_id>/', views.cardiovascular_view, name='cardiovascular_view'),
    path('medico/laboratorio/<int:jugador_id>/<int:registro_id>/', views.laboratorio_view, name='laboratorio_view'),
    path('medico/torax/<int:jugador_id>/<int:registro_id>/', views.torax_view, name='torax_view'),
    path('medico/oftalmologico/<int:jugador_id>/<int:registro_id>/', views.oftalmologico_view, name='oftalmologico_view'),
     path(
        'cargar-estudios/',
        MedicoCargarEstudiosView.as_view(),
        name='medico_cargar_estudios'
    ),
    path(
    "observaciones/",
    MedicoObservacionesPersonaView.as_view(),
    name="medico_observaciones_persona"
    ),


    path('ficha_medica/<int:registro_id>/', views.ficha_medica_views, name='ficha_medica'),
    path('eliminar-ficha/<int:jugador_id>/', views.eliminar_ficha_medica, name='eliminar_ficha_medica'),
    # Path para la vista de home de medico
    path('cus_home/', CusHomeView.as_view(),   name='cus_home'),
    path('cus/update/<int:cus_id>/', views.cus_update_view, name='cus_update_view'),
    path('cus/vista/<int:cus_id>/', views.cus_views, name='cus_views'),
    path('seleccionar_apto/', views.seleccionar_apto, name='seleccionar_apto'),
    path('cus/form/<int:estudiante_id>/', cus_form_view, name='cus_form_view'),
    path('documentacion/cargar/', views.cargar_documentacion, name='cargar_documentacion'),
    path('verificar-qr/', views.verificar_qr_pdf, name='verificar_qr_pdf'),
    path('contrato/', views.contrato, name='contrato'),


    # PATH RUTA MEDICOS APTOS GENERALES
    path("aptos_generales/",MedicoAptosGeneralesHomeView.as_view(),name="medico_aptos_generales_home"),
    path("apto/<int:apto_id>/update/",views.apto_general_update_view,name="apto_general_update_view"),
    path('apto/<int:apto_id>/ficha/', views.ficha_apto_general_view, name='ficha_apto_general_view'),

    # VALIDACION DELCODIGO QR
    path("validar-apto/", views.buscar_apto_general_view, name="buscar_apto_general"),
    #path("validar-apto/<int:apto_id>/", views.validar_apto_general_view, name="validar_apto_general"),

    path("validar-certificado/<str:tipo>/<int:id_certificado>/", validar_certificado_view, name="validar_certificado"),



]
