from django.urls import path

from .views import (
    CargarAntecedenteView,
    VerAntecedenteView,
    ModificarAntecedenteView,
    ActualizarConsentimientoView,
    CargarEstudioView,
    EstudiosMedicoListView,
    EliminarEstudioView,
    EliminarEstudioMedicoView,
    HistorialAptosView,

)
from . import views


app_name = 'registroMedico'

urlpatterns = [
    # crud antecedentes medicos
    path('cargar_antecedente/<int:jugador_id>/', CargarAntecedenteView.as_view(), name='cargar_antecedente'),
    path('ver_antecedente/<int:jugador_id>/', VerAntecedenteView.as_view(), name='ver_antecedente'),
    path('modificar_antecedente/<int:antecedente_id>/', ModificarAntecedenteView.as_view(), name='modificar_antecedente'),
    path('actualizar_consentimiento/<int:pk>/', ActualizarConsentimientoView.as_view(), name='consentimiento'),
    path('cron/enviar-notificaciones/', views.enviar_notificaciones_diarias, name='enviar_notificaciones_diarias'),
    # crud estudios medicos
    path('cargar_estudios/<int:jugador_id>/', CargarEstudioView.as_view(), name='cargar_estudio'),
    path('ver_estudios/<int:jugador_id>/', EstudiosMedicoListView.as_view(), name='ver_estudios'),
    path('eliminar_estudio/<int:pk>/', EliminarEstudioView.as_view(), name='eliminar_estudio'),
    path('eliminar-estudio/<int:pk>/', EliminarEstudioMedicoView.as_view(), name='eliminar_estudio_medico'),


    # historial
    path('historial/<int:jugador_id>/', HistorialAptosView.as_view(), name='ver_historial_aptos'),


]