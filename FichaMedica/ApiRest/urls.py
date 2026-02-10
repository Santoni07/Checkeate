from django.urls import path
from ApiRest.views.me import mis_aptos
from ApiRest.views.aptos import detalle_apto_general
urlpatterns = [
    path("me/aptos/", mis_aptos, name="api_me_aptos"),
    path("aptos/general/<int:id>/", detalle_apto_general),
]