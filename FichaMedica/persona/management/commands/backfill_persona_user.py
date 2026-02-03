from django.core.management.base import BaseCommand
from django.db import transaction
from persona.models import Persona


class Command(BaseCommand):
    help = "Backfill Persona.user desde Persona.profile.user (safe)"

    def handle(self, *args, **options):
        personas = Persona.objects.filter(
            user__isnull=True,
            profile__isnull=False
        )

        self.stdout.write(f"🔎 Personas a procesar: {personas.count()}")

        with transaction.atomic():
            for persona in personas:
                user = persona.profile.user

                # ¿Ya existe una Persona para este user?
                existente = Persona.objects.filter(user=user).first()

                if existente:
                    # Reasociamos el profile a la Persona existente
                    persona.profile = None
                    persona.save(update_fields=["profile"])
                    self.stdout.write(
                        f"↪ Persona {persona.id} ignorada (user ya tiene Persona {existente.id})"
                    )
                else:
                    persona.user = user
                    persona.save(update_fields=["user"])
                    self.stdout.write(
                        f"✔ Persona {persona.id} asociada a user {user.email}"
                    )

        self.stdout.write(self.style.SUCCESS("🎉 Backfill seguro completado"))
