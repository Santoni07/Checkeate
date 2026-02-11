from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


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
