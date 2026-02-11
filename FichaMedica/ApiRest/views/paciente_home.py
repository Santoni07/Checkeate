from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from aptos_generales.models import AptoGeneral
from persona.models import *
from datetime import timedelta
from django.utils import timezone

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def paciente_home(request):

    try:
        jugador = Jugador.objects.select_related(
            "persona__profile"
        ).get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return Response({"detail": "Paciente no encontrado"}, status=404)

    hoy = timezone.now().date()
    proximos_15 = hoy + timedelta(days=15)

    aptos = AptoGeneral.objects.filter(jugador=jugador)

    aptos_vigentes = aptos.filter(
        estado="APROBADA",
        fecha_caducidad__gte=hoy
    )

    aptos_aprobados = aptos.filter(
        estado="APROBADA"
    )

    # ================= ESTADO GENERAL =================
    if aptos_vigentes.exists():
        estado_general = "OK"
    elif aptos_aprobados.exists():
        estado_general = "VENCIDO"
    else:
        estado_general = "PARCIAL"

    # ================= ALERTAS =================
    alertas = []

    if aptos.filter(
        estado="APROBADA",
        fecha_caducidad__range=[hoy, proximos_15]
    ).exists():
        alertas.append({
            "tipo": "vencimiento",
            "mensaje": "Tenés un apto general que vence en los próximos 15 días"
        })

    # ================= PRÓXIMO VENCIMIENTO =================
    fechas_vencimiento = list(
        aptos.filter(
            estado="APROBADA",
            fecha_caducidad__gte=hoy
        ).values_list("fecha_caducidad", flat=True)
    )

    proximo_vencimiento = min(fechas_vencimiento) if fechas_vencimiento else None

    data = {
        "perfil": {
            "id": jugador.id,
            "nombre": jugador.persona.profile.nombre,
            "apellido": jugador.persona.profile.apellido,
            "dni": jugador.persona.profile.dni,
        },
        "resumen": {
            "aptos_generales": aptos.count(),
            "aptos_generales_vigentes": aptos_vigentes.count(),
        },
        "estado_general": estado_general,
        "proximo_vencimiento": proximo_vencimiento,
        "alertas": alertas
    }

    return Response(data)