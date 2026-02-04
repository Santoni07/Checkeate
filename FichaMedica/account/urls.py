from django.urls import path
from django.contrib.auth.views import LogoutView  # Importa LogoutView
from .views import *
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('login/', user_login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('register_alumnos/', register, name='register_alumnos'),
    path('logout/', views.logout_view, name='logout'),
    path('select_role/', select_role, name='select_role'),
    path('register_medico/', register_medico, name='register_medico'),
    path('register_paciente/', register, name='register_paciente'),
    
    #path verificar email por primera vez 
      path(
        "registro/verificar-email/",
        verificar_email_registro,
        name="verificar_email_registro"
    ),




    path('recuperar/', enviar_recuperacion_view, name='enviar_recuperacion'),
    path('account/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    path('recuperacion/enviado/', TemplateView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('check_session/', views.check_session, name='check_session'),
    path('terminos_condiciones/', views.terminos_condiciones, name='terminos_condiciones'),
    path('verificar-email/', views.verificar_email, name='verificar_email'),
    path('verificar-dni/', views.verificar_dni, name='verificar_dni'),

    ]