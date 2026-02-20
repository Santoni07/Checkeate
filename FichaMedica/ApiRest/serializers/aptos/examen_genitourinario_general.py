from rest_framework import serializers
from aptos_generales.models import ExamenGenitourinarioGeneral


class ExamenGenitourinarioGeneralSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamenGenitourinarioGeneral
        exclude = ["apto"]
