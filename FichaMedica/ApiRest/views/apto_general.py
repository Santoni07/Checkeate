from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from Medico.views import ficha_apto_general_view
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from aptos_generales.models import EstudiosAptoGeneral
from weasyprint import HTML
from django.http import FileResponse
from ApiRest.serializers.aptos import *

from aptos_generales.models import (
    AptoGeneral,
    
)
from persona.models import Jugador
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_apto_general_mobile(request, id):

    jugador = get_object_or_404(
        Jugador.objects.select_related("persona__profile"),
        persona__user=request.user
    )

    apto = get_object_or_404(
        AptoGeneral.objects.select_related("actividad", "medico"),
        id=id,
        jugador=jugador
    )

    # 🔥 ESTA ES TU VISTA WEB REAL
    ficha_url = request.build_absolute_uri(
        reverse("ficha_apto_general_view", args=[apto.id])
    )

    data = {
        "tipo": "APTO_GENERAL",

        "apto": AptoGeneralSerializer(apto).data,

        "actividad": {
            "id": apto.actividad.id if apto.actividad else None,
            "nombre": apto.actividad.nombre if apto.actividad else None,
        },

        "jugador": {
            "id": jugador.id,
            "nombre": jugador.persona.profile.nombre,
            "apellido": jugador.persona.profile.apellido,
            "dni": jugador.persona.profile.dni,
            "edad": jugador.persona.profile.edad,
        },

        "medico": {
            "id": apto.medico.id if apto.medico else None,
            "nombre": str(apto.medico) if apto.medico else None,
        },

        "antecedentes": (
            AntecedenteAptoGeneralSerializer(apto.antecedentes_snapshot).data
            if hasattr(apto, "antecedentes_snapshot") else None
        ),

        "examenes": {
            "fisico": (
                ExamenFisicoGeneralSerializer(apto.examen_fisico).data
                if hasattr(apto, "examen_fisico") else None
            ),
            "cardiovascular": (
                ExamenCardiovascularGeneralSerializer(apto.examen_cardiovascular).data
                if hasattr(apto, "examen_cardiovascular") else None
            ),
            "respiratorio": (
                ExamenRespiratorioGeneralSerializer(apto.examen_respiratorio).data
                if hasattr(apto, "examen_respiratorio") else None
            ),
            "abdomen": (
                ExamenAbdomenGeneralSerializer(apto.examen_abdomen).data
                if hasattr(apto, "examen_abdomen") else None
            ),
            "genitourinario": (
                ExamenGenitourinarioGeneralSerializer(apto.examen_genitourinario).data
                if hasattr(apto, "examen_genitourinario") else None
            ),
            "soma": (
                ExamenSomaGeneralSerializer(apto.examen_soma).data
                if hasattr(apto, "examen_soma") else None
            ),
        },

        "motivo_actividad": (
            MotivoActividadGeneralSerializer(apto.motivo_actividad).data
            if hasattr(apto, "motivo_actividad") else None
        ),

        "estudios": EstudiosAptoGeneralSerializer(
            apto.estudios_apto.all(),
            many=True
        ).data,

        "pdf": {
    "ver": request.build_absolute_uri(
        reverse("api_descargar_pdf_apto_general", args=[apto.id])
    ),
    "descargar": request.build_absolute_uri(
        reverse("api_descargar_pdf_apto_general", args=[apto.id])
    ),
    "requiere_login": True
}
    }

    return Response(data)

# ============================================================
# 📥 DESCARGAR PDF APTO GENERAL (JWT PROTEGIDO)
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def descargar_pdf_apto_general(request, id):

    jugador = get_object_or_404(
        Jugador.objects.select_related("persona__profile"),
        persona__user=request.user
    )

    apto = get_object_or_404(
        AptoGeneral,
        id=id,
        jugador=jugador
    )

    # 🔥 Forzamos el parámetro descargar_pdf=true
    request.GET._mutable = True
    request.GET['descargar_pdf'] = 'true'

    return ficha_apto_general_view(request, apto_id=id)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def paciente_estudios_apto(request):

    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"estudios": []})

    estudios = EstudiosAptoGeneral.objects.filter(
        apto__jugador=jugador
    ).select_related("apto").order_by("-fecha_creacion")

    return Response({
        "estudios": EstudiosAptoGeneralSerializer(estudios, many=True).data
    })
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def descargar_pdf_estudio_apto(request, id):

    jugador = get_object_or_404(
        Jugador,
        persona__user=request.user
    )

    estudio = get_object_or_404(
        EstudiosAptoGeneral,
        idestudio=id,
        apto__jugador=jugador
    )

    if not estudio.archivo:
        return Response({"detail": "Archivo no encontrado"}, status=404)

    return FileResponse(
        estudio.archivo.open("rb"),
        as_attachment=False
    )