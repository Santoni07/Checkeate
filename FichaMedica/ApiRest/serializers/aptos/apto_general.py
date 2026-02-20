from rest_framework import serializers
from aptos_generales.models import AptoGeneral


class AptoGeneralSerializer(serializers.ModelSerializer):

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True
    )

    class Meta:
        model = AptoGeneral
        fields = [
            "id",
            "estado",
            "estado_display",
            "fecha_creacion",
            "fecha_caducidad",
            "fecha_de_llenado",
            "observacion",
            "consentimiento_persona",
        ]
