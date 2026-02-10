from rest_framework import serializers
from RegistroMedico.models import ElectroEsfuerzo


class ElectroEsfuerzoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectroEsfuerzo
        exclude = ["idelectro_esfuerzo", "ficha_medica"]