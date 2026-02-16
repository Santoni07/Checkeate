from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from persona.models import Profile


@api_view(["POST"])
@permission_classes([AllowAny])
def verificar_email(request):

    email = request.data.get("email")

    if not email:
        return Response(
            {"detail": "email es requerido"},
            status=400
        )

    try:
        user = User.objects.get(email=email)

        profiles = Profile.objects.filter(user=user)

        roles = [
            {
                "profile_id": p.id,
                "codigo": p.rol,
                "label": p.get_rol_display() if hasattr(p, "get_rol_display") else p.rol
            }
            for p in profiles
        ]

        return Response({
            "existe": True,
            "mensaje": "El usuario ya existe",
            "roles": roles
        })

    except User.DoesNotExist:
        return Response({
            "existe": False,
            "mensaje": "Email disponible"
        })
