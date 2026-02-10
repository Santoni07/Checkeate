from rest_framework import serializers
from RegistroMedico.models import Cardiovascular


class CardiovascularSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cardiovascular
        exclude = ["idcardiovascular", "ficha_medica"]