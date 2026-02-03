from django.conf import settings

from django.db import models



class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Permitir múltiples perfiles para un usuario
    nombre = models.CharField(max_length=30, blank=True, null=True)
    apellido = models.CharField(max_length=30, blank=True, null=True)
    dni = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    email = models.EmailField(max_length=254)  # Eliminar unique=True para permitir múltiples perfiles con el mismo email

    rol = models.CharField(
        max_length=20,
        choices=[
            ('jugador', 'Jugador'),
            ('medico', 'Médico'),
            ('representante', 'Representante'),
            ('colegio' , 'Colegio'),
            ('estudiante', 'Estudiante'),
            ('paciente', 'Paciente'),
            ('actividad', 'Actividad'),

        ],
        default='jugador'
    )

    class Meta:
        unique_together = ('user', 'rol')  # Garantiza que un usuario solo tenga un perfil por rol

    @property
    def edad(self):
        from datetime import date
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    def save(self, *args, **kwargs):
        # 🚫 Evitar guardar perfiles sin rol o con datos vacíos automáticos
        if not self.rol:
            self.rol = 'jugador'  # por compatibilidad, pero no lo creamos vacío

        # Evitar perfiles automáticos sin nombre y apellido
        if not self.nombre and not self.apellido and not self.dni:
            print(f"⚠️ Previniendo guardado de Profile vacío para user={self.user.email}")
            return  # evita crear registros basura

        # Capitalización
        if self.nombre:
            self.nombre = self.nombre.capitalize()
        if self.apellido:
            self.apellido = self.apellido.capitalize()

        # Sincronizar email
        if self.user and self.user.email != self.email:
            self.user.email = self.email
            self.user.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.rol}"