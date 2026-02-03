from .models import *

def get_persona_from_user(user):
    persona, created = Persona.objects.get_or_create(
        user=user,
        defaults={
            "telefono_alternativo": "S/D"
        }
    )
    return persona