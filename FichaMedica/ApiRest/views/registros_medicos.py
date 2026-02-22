from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from RegistroMedico.models import EstudiosMedico
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from weasyprint import HTML

from persona.models import Jugador, JugadorCategoriaEquipo
from RegistroMedico.models import (
    RegistroMedico,
   
    EstudiosMedico
)

from ApiRest.serializers.registro_medico import RegistroMedicoSerializer
from ApiRest.serializers.antecedente_enfermedades import AntecedenteEnfermedadesSerializer
from ApiRest.serializers.electro_basal import ElectroBasalSerializer
from ApiRest.serializers.electro_esfuerzo import ElectroEsfuerzoSerializer
from ApiRest.serializers.cardiovascular import CardiovascularSerializer
from ApiRest.serializers.laboratorio import LaboratorioSerializer
from ApiRest.serializers.torax import ToraxSerializer
from ApiRest.serializers.oftalmologico import OftalmologicoSerializer
from ApiRest.serializers.otros_examenes import OtrosExamenesClinicosSerializer
from ApiRest.serializers.estudios_medico import EstudiosMedicoSerializer


# ============================================================
# 🔎 DETALLE REGISTRO MEDICO (JSON)
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_registro_medico(request, id):

    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    registro = (
        RegistroMedico.objects
        .filter(id=id, jugador=jugador)
        .select_related("torneo", "competencia", "medico")
        .first()
    )

    if not registro:
        return Response({"detail": "Registro médico no encontrado"}, status=404)

    base_url = request.build_absolute_uri(
        reverse("ficha_medica", args=[registro.id])
    )

    jce = (
        JugadorCategoriaEquipo.objects
        .select_related(
            "categoria_equipo__categoria",
            "categoria_equipo__equipo",
            "categoria_equipo__categoria__torneo"
        )
        .filter(
            jugador=jugador,
            categoria_equipo__categoria__torneo=registro.torneo
        )
        .first()
    )

    data = {
        "tipo": "REGISTRO_MEDICO",

        "registro": RegistroMedicoSerializer(registro).data,

        "evento": {
            "torneo": (
                {
                    "id": registro.torneo.id,
                    "nombre": registro.torneo.nombre,
                }
                if registro.torneo else None
            ),
            "competencia": (
                {
                    "id": registro.competencia.id,
                    "nombre": registro.competencia.nombre,
                }
                if registro.competencia else None
            ),
            "categoria": (
                {
                    "id": jce.categoria_equipo.categoria.id,
                    "nombre": jce.categoria_equipo.categoria.nombre,
                }
                if jce else None
            ),
            "equipo": (
                {
                    "id": jce.categoria_equipo.equipo.id,
                    "nombre": jce.categoria_equipo.equipo.nombre,
                }
                if jce else None
            ),
        },

        "jugador": {
            "id": jugador.id,
            "nombre": jugador.persona.profile.nombre,
            "apellido": jugador.persona.profile.apellido,
            "dni": jugador.persona.profile.dni,
            "edad": jugador.persona.profile.edad,
        },

        "medico": {
            "id": registro.medico.id if registro.medico else None,
            "nombre": str(registro.medico) if registro.medico else None,
        },

        "antecedentes": (
            AntecedenteEnfermedadesSerializer(jugador.antecedentes).data
            if hasattr(jugador, "antecedentes") else None
        ),

        "examenes": {
            "electro_basal": (
                ElectroBasalSerializer(registro.electrobasal).data
                if hasattr(registro, "electrobasal") else None
            ),
            "electro_esfuerzo": (
                ElectroEsfuerzoSerializer(registro.electroesfuerzo).data
                if hasattr(registro, "electroesfuerzo") else None
            ),
            "cardiovascular": (
                CardiovascularSerializer(registro.cardiovascular).data
                if hasattr(registro, "cardiovascular") else None
            ),
            "laboratorio": (
                LaboratorioSerializer(registro.laboratorio).data
                if hasattr(registro, "laboratorio") else None
            ),
            "torax": (
                ToraxSerializer(registro.torax).data
                if hasattr(registro, "torax") else None
            ),
            "oftalmologico": (
                OftalmologicoSerializer(registro.oftalmologico).data
                if hasattr(registro, "oftalmologico") else None
            ),
            "otros": (
                OtrosExamenesClinicosSerializer(registro.otros_examenes).data
                if hasattr(registro, "otros_examenes") else None
            ),
        },

        "estudios": EstudiosMedicoSerializer(
            EstudiosMedico.objects.filter(jugador=jugador),
            many=True
        ).data,

        "pdf": {
            "ver": base_url,
            "descargar": f"{base_url}?descargar_pdf=true",
            "requiere_login": True
        }
    }

    return Response(data)


# ============================================================
# 📄 GENERADOR PDF REUTILIZABLE
# ============================================================

def generar_pdf_registro(registro, request):

    context = {
        "registro": registro,
        "jugador": registro.jugador,
        "torneo": registro.torneo,
        "competencia": registro.competencia,
    }

    html_string = render_to_string("registroMedico/ficha_medica.html", context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="ficha_medica_{registro.id}.pdf"'

    return response


# ============================================================
# 📥 DESCARGAR PDF PARA MOBILE (JWT PROTEGIDO)
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def descargar_pdf_registro(request, id):

    jugador = get_object_or_404(
        Jugador.objects.select_related("persona__user"),
        persona__user=request.user
    )

    registro = get_object_or_404(
        RegistroMedico,
        id=id,
        jugador=jugador
    )

    return generar_pdf_registro(registro, request)

from django.http import FileResponse

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def descargar_estudio_registro(request, id):

    jugador = get_object_or_404(
        Jugador,
        persona__user=request.user
    )

    estudio = get_object_or_404(
        EstudiosMedico,
        idestudio=id,   # ⚠️ usamos idestudio
        jugador=jugador
    )

    if not estudio.archivo:
        return Response(
            {"detail": "El estudio no tiene archivo adjunto"},
            status=404
        )

    return FileResponse(
        estudio.archivo.open("rb"),
        as_attachment=True,
        filename=estudio.archivo.name.split("/")[-1]
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_estudios_registro(request):

    jugador = get_object_or_404(
        Jugador,
        persona__user=request.user
    )

    estudios = EstudiosMedico.objects.filter(jugador=jugador)

    data = [
    {
        "idestudio": e.idestudio,
        "tipo_estudio": e.get_tipo_estudio_display(),
        "fecha_caducidad": e.fecha_caducidad,
        "fecha_creacion": e.fecha_creacion,
        "observaciones": e.observaciones,
        "filename": e.archivo.name.split("/")[-1] if e.archivo else None,
        "tiene_archivo": bool(e.archivo),
    }
    for e in estudios
]

    return Response({"estudios": data})