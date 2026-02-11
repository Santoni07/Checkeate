from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ApiRest.serializers.apto import AptoResumenSerializer
from aptos_generales.models import AptoGeneral
from RegistroMedico.models import RegistroMedico
from persona.models import Jugador
from Medico.models import Medico 
from account.models import Profile


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_roles(request):
    user = request.user

    profiles = Profile.objects.filter(user=user)

    roles = []

    for profile in profiles:
        if profile.rol == "jugador":
            roles.append({
                "codigo": "jugador",
                "label": "Jugador",
                "profile_id": profile.id,
                "home": "/api/jugador/home/"
            })

        elif profile.rol == "paciente":
            roles.append({
                "codigo": "paciente",
                "label": "Paciente",
                "profile_id": profile.id,
                "home": "/api/paciente/home/"
            })

        elif profile.rol == "medico":
            roles.append({
                "codigo": "medico",
                "label": "Médico",
                "profile_id": profile.id,
                "home": "/api/medico/home/"
            })

    return Response({
        "usuario": {
            "id": user.id,
            "email": user.email,
        },
        "roles": roles
    })


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seleccionar_rol(request):

    profile_id = request.data.get("profile_id")

    if not profile_id:
        return Response(
            {"detail": "profile_id es requerido"},
            status=400
        )

    try:
        profile = Profile.objects.get(
            id=profile_id,
            user=request.user
        )
    except Profile.DoesNotExist:
        return Response(
            {"detail": "Perfil inválido"},
            status=403
        )

    # Determinar a dónde debe ir
    if profile.rol == "jugador":
        home = "/api/jugador/home/"
    elif profile.rol == "paciente":
        home = "/api/paciente/home/"
    elif profile.rol == "representante":
        home = "/api/representante/home/"
    else:
        home = None

    return Response({
        "rol_activo": {
            "profile_id": profile.id,
            "codigo": profile.rol,
            "label": profile.get_rol_display() if hasattr(profile, "get_rol_display") else profile.rol,
            "home": home
        }
    })