from rest_framework import serializers
from aptos_generales.models import EstudiosAptoGeneral

class EstudiosAptoGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudiosAptoGeneral
        exclude = ("apto",)
