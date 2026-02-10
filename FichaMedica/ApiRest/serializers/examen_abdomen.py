from rest_framework import serializers
from aptos_generales.models import ExamenAbdomenGeneral

class ExamenAbdomenGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenAbdomenGeneral
        exclude = ("id", "apto")
