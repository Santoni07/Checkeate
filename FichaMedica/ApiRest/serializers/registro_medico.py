from rest_framework import serializers
from RegistroMedico.models import RegistroMedico


class RegistroMedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroMedico
        fields = [
            "id",
            "estado",
            "fecha_creacion",
            "fecha_caducidad",
            "fecha_de_llenado",
            "observacion",
            "consentimiento_persona",
        ]
