from rest_framework import serializers
from RegistroMedico.models import Oftalmologico


class OftalmologicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oftalmologico
        exclude = ["idoftalmologico", "ficha_medica"]