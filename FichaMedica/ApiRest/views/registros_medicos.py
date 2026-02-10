from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from persona.models import Jugador
from RegistroMedico.models import (
    RegistroMedico,
    AntecedenteEnfermedades,
    ElectroBasal,
    ElectroEsfuerzo,
    Cardiovascular,
    Laboratorio,
    Torax,
    Oftalmologico,
    OtrosExamenesClinicos,
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_registro_medico(request, id):

    # ===================== JUGADOR =====================
    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    # ===================== REGISTRO =====================
    registro = (
        RegistroMedico.objects
        .filter(id=id, jugador=jugador)
        .select_related("torneo", "competencia", "medico")
        .first()
    )

    if not registro:
        return Response({"detail": "Registro médico no encontrado"}, status=404)

    # ===================== PDF (WEB) =====================
    base_url = request.build_absolute_uri(
        reverse("ficha_medica", args=[registro.id])
    )

    # ===================== RESPONSE =====================
    data = {
        "tipo": "REGISTRO_MEDICO",

        "registro": RegistroMedicoSerializer(registro).data,

        "evento": {
            "torneo": registro.torneo.nombre if registro.torneo else None,
            "competencia": registro.competencia.nombre if registro.competencia else None,
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
