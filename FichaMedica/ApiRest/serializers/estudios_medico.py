from rest_framework import serializers
from RegistroMedico.models import EstudiosMedico


class EstudiosMedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudiosMedico
        fields = [
            "idestudio",
            "tipo_estudio",
            "observaciones",
            "fecha_creacion",
            "fecha_caducidad",
            "archivo",
        ]
