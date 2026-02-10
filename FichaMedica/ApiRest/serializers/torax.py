from rest_framework import serializers
from RegistroMedico.models import Torax


class ToraxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Torax
        exclude = ["idtorax", "ficha_medica"]