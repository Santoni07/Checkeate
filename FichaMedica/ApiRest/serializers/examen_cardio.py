from rest_framework import serializers
from aptos_generales.models import ExamenCardiovascularGeneral

class ExamenCardiovascularGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenCardiovascularGeneral
        exclude = ("id", "apto")