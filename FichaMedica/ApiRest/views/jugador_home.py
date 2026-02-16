from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from persona.models import Jugador
from RegistroMedico.models import RegistroMedico
from ApiRest.utils import get_active_profile


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def jugador_home(request):

    # 🔹 Obtener rol activo desde header
    profile = get_active_profile(request)

    if profile.rol != "jugador":
        return Response({"detail": "Rol incorrecto"}, status=403)

    # 🔹 Obtener persona única del user
    try:
        persona = request.user.persona
    except:
        return Response({"detail": "Persona no encontrada"}, status=404)

    # 🔹 Obtener jugador asociado a la persona
    try:
        jugador = Jugador.objects.get(persona=persona)
    except Jugador.DoesNotExist:
        return Response({"detail": "Jugador no encontrado"}, status=404)

    hoy = timezone.now().date()
    proximos_15 = hoy + timedelta(days=15)

    registros = RegistroMedico.objects.filter(jugador=jugador)

    registros_vigentes = registros.filter(
        estado="APROBADA",
        fecha_caducidad__gte=hoy
    )

    registros_aprobados = registros.filter(
        estado="APROBADA"
    )

    if registros_vigentes.exists():
        estado_general = "OK"
    elif registros_aprobados.exists():
        estado_general = "VENCIDO"
    else:
        estado_general = "PARCIAL"

    alertas = []

    if registros.filter(
        estado="APROBADA",
        fecha_caducidad__range=[hoy, proximos_15]
    ).exists():
        alertas.append({
            "tipo": "vencimiento",
            "mensaje": "Tenés un registro médico que vence en los próximos 15 días"
        })

    fechas_vencimiento = list(
        registros.filter(
            estado="APROBADA",
            fecha_caducidad__gte=hoy
        ).values_list("fecha_caducidad", flat=True)
    )

    proximo_vencimiento = min(fechas_vencimiento) if fechas_vencimiento else None

    data = {
        "perfil": {
            "id": jugador.id,
            "nombre": profile.nombre,
            "apellido": profile.apellido,
            "dni": profile.dni,
        },
        "resumen": {
            "registros_medicos": registros.count(),
            "registros_vigentes": registros_vigentes.count(),
        },
        "estado_general": estado_general,
        "proximo_vencimiento": proximo_vencimiento,
        "alertas": alertas
    }

    return Response(data)
