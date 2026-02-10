from rest_framework import serializers
from aptos_generales.models import AntecedenteAptoGeneral

class AntecedenteAptoGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedenteAptoGeneral
        exclude = ("id", "apto", "jugador", "creado_en")