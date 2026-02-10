from rest_framework import serializers
from RegistroMedico.models import OtrosExamenesClinicos


class OtrosExamenesClinicosSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtrosExamenesClinicos
        exclude = ["id", "ficha_medica"]
