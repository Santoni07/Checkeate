from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.urls import reverse
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

    # ===================== JUGADOR =====================
    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    # ===================== APTO =====================
    apto = (
        AptoGeneral.objects
        .filter(id=id, jugador=jugador)
        .select_related("actividad", "medico")
        .first()
    )

    if not apto:
        return Response({"detail": "Apto no encontrado"}, status=404)

    # ===================== JUGADOR DATA =====================
    jugador_data = {
        "id": jugador.id,
        "nombre": jugador.persona.profile.nombre,
        "apellido": jugador.persona.profile.apellido,
        "dni": jugador.persona.profile.dni,
        "edad": jugador.persona.profile.edad,
    }

    # ===================== PDF LINKS (WEB EXISTENTE) =====================
    base_url = request.build_absolute_uri(
        reverse("ficha_apto_general_view", args=[apto.id])
    )

    pdf_data = {
        "ver": base_url,  # abre HTML (como en la web)
        "descargar": f"{base_url}?descargar_pdf=true",  # descarga PDF
        "requiere_login": True
    }

    # ===================== RESPONSE =====================
    data = {
        "tipo": "APTO_GENERAL",

        "apto": AptoGeneralSerializer(apto).data,

        "actividad": {
            "id": apto.actividad.id if apto.actividad else None,
            "nombre": apto.actividad.nombre if apto.actividad else None,
        },

        "jugador": jugador_data,

        "medico": {
            "id": apto.medico.id if apto.medico else None,
            "nombre": str(apto.medico) if apto.medico else None,
        },

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
        ).data,

        "pdf": pdf_data
    }

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_aptos_general(request):

    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    aptos = (
        AptoGeneral.objects
        .filter(jugador=jugador)
        .select_related("actividad")
        .order_by("-fecha_creacion")
    )

    data = [
    {
        "id": apto.id,
        "actividad": apto.actividad.nombre if apto.actividad else None,
        "estado": apto.estado,
        "fecha_inscripcion": (
            apto.fecha_creacion.strftime("%Y-%m-%d")
            if apto.fecha_creacion else None
        ),
        "fecha_vencimiento": (
            apto. fecha_caducidad.strftime("%Y-%m-%d")
            if apto. fecha_caducidad else None
        ),
        "antecedentes_ok": hasattr(apto, "antecedentes_snapshot"),
    }
    for apto in aptos
]

    return Response({"aptos": data})