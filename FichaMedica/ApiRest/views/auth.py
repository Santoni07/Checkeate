from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from persona.models import Persona
from account.models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):

    email = request.data.get("email")
    password = request.data.get("password")
    rol = request.data.get("rol_asignado")

    if not email or not password or not rol:
        return Response(
            {"detail": "email, password y rol_asignado son requeridos"},
            status=400
        )

    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            "email": email,
            "password": make_password(password)
        }
    )

    # Si el usuario ya existía y está intentando registrarse otra vez
    if not created:
        if not user.check_password(password):
            return Response(
                {"detail": "La contraseña es incorrecta"},
                status=400
            )

    # Crear profile si no existe con ese rol
    profile = Profile.objects.filter(user=user, rol=rol).first()

    if not profile:
        profile = Profile.objects.create(
            user=user,
            rol=rol
        )

    # Crear persona solo si no existe
    persona = Persona.objects.filter(user=user).first()

    if not persona:
        persona = Persona.objects.create(
            user=user,
            profile=profile
        )

    token, _ = Token.objects.get_or_create(user=user)

    # Determinar home
    if rol == "jugador":
        home = "/api/jugador/home/"
    elif rol == "paciente":
        home = "/api/paciente/home/"
    elif rol == "representante":
        home = "/api/representante/home/"
    else:
        home = None

    return Response({
        "token": token.key,
        "usuario": {
            "id": user.id,
            "email": user.email,
        },
        "rol_creado": {
            "profile_id": profile.id,
            "codigo": rol,
            "home": home
        }
    })

@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):

    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"detail": "Email y password requeridos"}, status=400)

    user = authenticate(username=email, password=password)

    if not user:
        return Response({"detail": "Credenciales inválidas"}, status=401)

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,
        "user_id": user.id,
        "email": user.email
    })
