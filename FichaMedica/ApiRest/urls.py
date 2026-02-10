from django.urls import path
from ApiRest.views.me import mis_aptos

urlpatterns = [
    path("me/aptos/", mis_aptos, name="api_me_aptos"),
]