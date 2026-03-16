from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from ApiRest.serializers.antecedente_apto import AntecedenteAptoGeneralSerializer
from persona.models import Jugador, JugadorCategoriaEquipo
from RegistroMedico.models import RegistroMedico
from ApiRest.utils import get_active_profile



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_registros_medicos(request):
    try:
        jugador = Jugador.objects.get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    registros = (
        RegistroMedico.objects
        .filter(jugador=jugador)
        .select_related("torneo")
        .order_by("-fecha_creacion")
    )

    data = []

    for r in registros:
        jce = (
            JugadorCategoriaEquipo.objects
            .select_related(
                "categoria_equipo__categoria",
                "categoria_equipo__equipo"
            )
            .filter(
                jugador=jugador,
                categoria_equipo__categoria__torneo=r.torneo
            )
            .first()
        )

        data.append({
            "id": r.id,
            "torneo": r.torneo.nombre if r.torneo else None,
            "categoria": (
                jce.categoria_equipo.categoria.nombre
                if jce else None
            ),
            "equipo": (
                jce.categoria_equipo.equipo.nombre
                if jce else None
            ),
            "consentimiento": r.consentimiento_persona,
            "antecedentes_ok": hasattr(jugador, "antecedentes"),
            "estado": r.estado,
        })

    return Response({"registros": data})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen_antecedentes_jugador(request):

    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({
            "existe": False,
            "completo": False
        })

    antecedente = getattr(jugador, "antecedentes", None)

    if not antecedente:
        return Response({
            "existe": False,
            "completo": False
        })

    # 🔥 acá definimos qué es completo
    campos = [
        antecedente.es_diabetico,
        antecedente.fue_operado,
        antecedente.es_asmatico,
        antecedente.presion_arterial,
        antecedente.soplo_cardiaco,
    
    ]

    completo = any(campos)

    return Response({
        "existe": True,
        "completo": completo
    })
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_antecedente_jugador(request):

    jugador = Jugador.objects.get(persona__user=request.user)

    antecedente = getattr(jugador, "antecedentes", None)

    if not antecedente:
        return Response({"existe": False})

    serializer = AntecedenteAptoGeneralSerializer(antecedente)

    return Response(serializer.data)