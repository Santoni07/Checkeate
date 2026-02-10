from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ApiRest.serializers.apto import AptoResumenSerializer
from aptos_generales.models import AptoGeneral
from RegistroMedico.models import RegistroMedico
from persona.models import Jugador

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_aptos(request):
    user = request.user

    try:
        jugador = Jugador.objects.select_related("persona").get(persona__user=user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    aptos = []

    # Aptos generales
    for apto in AptoGeneral.objects.filter(jugador=jugador):
        aptos.append({
            "tipo": "GENERAL",
            "nombre": apto.actividad.nombre if hasattr(apto, "actividad") else "Apto General",
            "estado": apto.estado,
            "vencimiento": apto.fecha_caducidad,
            "uuid": apto.id,          # 👈 CAMBIO ACÁ
        })

    # Aptos por torneo
    for registro in RegistroMedico.objects.filter(jugador=jugador):
        aptos.append({
            "tipo": "TORNEO",
            "nombre": registro.torneo.nombre,
            "estado": registro.estado,
            "vencimiento": registro.fecha_caducidad,
            "uuid": registro.id,      # 👈 Y ACÁ
        })

    serializer = AptoResumenSerializer(aptos, many=True)
    return Response(serializer.data)