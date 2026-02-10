from rest_framework import serializers
from RegistroMedico.models import Laboratorio


class LaboratorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorio
        exclude = ["idlaboratorio", "ficha_medica"]