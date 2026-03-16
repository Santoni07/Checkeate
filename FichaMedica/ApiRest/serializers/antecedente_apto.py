from rest_framework import serializers
from RegistroMedico.models import AntecedenteEnfermedades

class AntecedenteAptoGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedenteEnfermedades
        fields="__all__"