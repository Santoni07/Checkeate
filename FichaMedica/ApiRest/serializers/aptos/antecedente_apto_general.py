from rest_framework import serializers
from aptos_generales.models import AntecedenteAptoGeneral


class AntecedenteAptoGeneralSerializer(serializers.ModelSerializer):

    esta_completo = serializers.SerializerMethodField()

    class Meta:
        model = AntecedenteAptoGeneral
        exclude = ["apto"]

    def get_esta_completo(self, obj):
        return obj.esta_completo()
