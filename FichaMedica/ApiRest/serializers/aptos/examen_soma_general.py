from rest_framework import serializers
from aptos_generales.models import ExamenSomaGeneral


class ExamenSomaGeneralSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamenSomaGeneral
        exclude = ["apto"]