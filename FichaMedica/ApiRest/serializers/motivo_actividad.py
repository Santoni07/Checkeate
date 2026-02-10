from rest_framework import serializers
from aptos_generales.models import MotivoActividadGeneral

class MotivoActividadGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoActividadGeneral
        exclude = ("id", "apto")
