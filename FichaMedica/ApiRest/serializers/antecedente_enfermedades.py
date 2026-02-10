from rest_framework import serializers
from RegistroMedico.models import AntecedenteEnfermedades


class AntecedenteEnfermedadesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedenteEnfermedades
        exclude = ["id", "jugador"]