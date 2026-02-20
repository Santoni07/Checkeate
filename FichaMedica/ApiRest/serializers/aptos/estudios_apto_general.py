from rest_framework import serializers
from aptos_generales.models import EstudiosAptoGeneral


class EstudiosAptoGeneralSerializer(serializers.ModelSerializer):

    tipo_estudio_display = serializers.CharField(
        source="get_tipo_estudio_display",
        read_only=True
    )

    class Meta:
        model = EstudiosAptoGeneral
        exclude = ["apto"]