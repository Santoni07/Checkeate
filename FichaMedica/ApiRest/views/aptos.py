from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from persona.models import Jugador
from aptos_generales.models import AptoGeneral

from ApiRest.serializers.apto_general import AptoGeneralSerializer
from ApiRest.serializers.antecedente_apto import AntecedenteAptoGeneralSerializer
from ApiRest.serializers.examen_fisico import ExamenFisicoGeneralSerializer
from ApiRest.serializers.examen_cardio import ExamenCardiovascularGeneralSerializer
from ApiRest.serializers.examen_respiratorio import ExamenRespiratorioGeneralSerializer
from ApiRest.serializers.examen_abdomen import ExamenAbdomenGeneralSerializer
from ApiRest.serializers.examen_genitourinario import ExamenGenitourinarioGeneralSerializer
from ApiRest.serializers.examen_soma import ExamenSomaGeneralSerializer
from ApiRest.serializers.motivo_actividad import MotivoActividadGeneralSerializer
from ApiRest.serializers.estudio_apto import EstudiosAptoGeneralSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_apto_general(request, id):
    try:
        jugador = Jugador.objects.get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    apto = AptoGeneral.objects.filter(
        id=id,
        jugador=jugador
    ).select_related(
        "actividad",
        "medico"
    ).first()

    if not apto:
        return Response({"detail": "Apto no encontrado"}, status=404)

    data = {
        "tipo": "GENERAL",
        "apto": AptoGeneralSerializer(apto).data,
        "antecedentes": (
            AntecedenteAptoGeneralSerializer(apto.antecedentes_snapshot).data
            if hasattr(apto, "antecedentes_snapshot") else None
        ),
        "examenes": {
            "fisico": ExamenFisicoGeneralSerializer(apto.examen_fisico).data if hasattr(apto, "examen_fisico") else None,
            "cardiovascular": ExamenCardiovascularGeneralSerializer(apto.examen_cardiovascular).data if hasattr(apto, "examen_cardiovascular") else None,
            "respiratorio": ExamenRespiratorioGeneralSerializer(apto.examen_respiratorio).data if hasattr(apto, "examen_respiratorio") else None,
            "abdomen": ExamenAbdomenGeneralSerializer(apto.examen_abdomen).data if hasattr(apto, "examen_abdomen") else None,
            "genitourinario": ExamenGenitourinarioGeneralSerializer(apto.examen_genitourinario).data if hasattr(apto, "examen_genitourinario") else None,
            "soma": ExamenSomaGeneralSerializer(apto.examen_soma).data if hasattr(apto, "examen_soma") else None,
        },
        "motivo_actividad": (
            MotivoActividadGeneralSerializer(apto.motivo_actividad).data
            if hasattr(apto, "motivo_actividad") else None
        ),
        "estudios": EstudiosAptoGeneralSerializer(
            apto.estudios_apto.all(), many=True
        ).data
    }

    return Response(data)
