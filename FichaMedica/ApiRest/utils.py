from account.models import Profile
from rest_framework.exceptions import PermissionDenied

def get_active_profile(request):
    profile_id = request.headers.get("X-Profile-Id")

    if not profile_id:
        raise PermissionDenied("X-Profile-Id header requerido")

    try:
        profile = Profile.objects.get(
            id=profile_id,
            user=request.user
        )
    except Profile.DoesNotExist:
        raise PermissionDenied("Perfil inválido")

    return profile
