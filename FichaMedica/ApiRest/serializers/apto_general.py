from rest_framework import serializers
from aptos_generales.models import AptoGeneral

class AptoGeneralSerializer(serializers.ModelSerializer):
    actividad = serializers.SerializerMethodField()
    medico = serializers.SerializerMethodField()

    class Meta:
        model = AptoGeneral
        fields = [
            "id",
            "estado",
            "fecha_creacion",
            "fecha_caducidad",
            "fecha_de_llenado",
            "observacion",
            "consentimiento_persona",
            "actividad",
            "medico",
        ]

    def get_actividad(self, obj):
        if obj.actividad:
            return {
                "id": obj.actividad.id,
                "nombre": obj.actividad.nombre
            }
        return None

    def get_medico(self, obj):
        if obj.medico:
            return {
                "id": obj.medico.id,
                "nombre": str(obj.medico)
            }
        return None
