from rest_framework import serializers
from aptos_generales.models import ExamenFisicoGeneral

class ExamenFisicoGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenFisicoGeneral
        exclude = ("id", "apto")
