from rest_framework import serializers

class AptoResumenSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    nombre = serializers.CharField()
    estado = serializers.CharField()
    vencimiento = serializers.DateField(allow_null=True)
    uuid = serializers.IntegerField()