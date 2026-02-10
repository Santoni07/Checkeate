from rest_framework import serializers
from aptos_generales.models import ExamenRespiratorioGeneral

class ExamenRespiratorioGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenRespiratorioGeneral
        exclude = ("id", "apto")