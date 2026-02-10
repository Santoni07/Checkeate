from django.urls import path
from ApiRest.views.me import mis_aptos
from ApiRest.views.aptos import detalle_apto_general
from ApiRest.views.registros_medicos import detalle_registro_medico

urlpatterns = [
    path("me/aptos/", mis_aptos, name="api_me_aptos"),
    path("aptos/general/<int:id>/", detalle_apto_general),
    path("registros-medicos/<int:id>/", detalle_registro_medico),

]