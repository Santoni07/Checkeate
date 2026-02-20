from rest_framework import serializers
from aptos_generales.models import ExamenFisicoGeneral


class ExamenFisicoGeneralSerializer(serializers.ModelSerializer):

    diagnostico_display = serializers.CharField(
        source="get_diagnostico_display",
        read_only=True
    )

    class Meta:
        model = ExamenFisicoGeneral
        exclude = ["apto"]
