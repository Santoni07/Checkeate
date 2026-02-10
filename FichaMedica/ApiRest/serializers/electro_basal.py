from rest_framework import serializers
from RegistroMedico.models import ElectroBasal


class ElectroBasalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectroBasal
        exclude = ["idelectro_basal", "ficha_medica"]
