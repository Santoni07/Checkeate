

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

SERVICIOS_ROLES = {
    "apto_general": "paciente",
    "torneo": "jugador",
    "cus": "estudiante",
    "medico": "medico",
    "representante": "representante",
}

@api_view(["POST"])
@permission_classes([AllowAny])
def seleccionar_servicio(request):

    servicio = request.data.get("servicio")

    if not servicio:
        return Response(
            {"detail": "El campo 'servicio' es requerido"},
            status=400
        )

    rol = SERVICIOS_ROLES.get(servicio)

    if not rol:
        return Response(
            {"detail": "Servicio inválido"},
            status=400
        )

    return Response({
        "servicio": servicio,
        "rol_asignado": rol,
        "mensaje": "Rol determinado correctamente. Continúe con el registro."
    })
