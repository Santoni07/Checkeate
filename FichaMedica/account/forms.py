
from django import forms
from django.contrib.auth.models import User
from .models import Profile

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Repite Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha de Nacimiento"
    )

    class Meta:
        model = Profile
        fields = [
            'nombre',
            'apellido',
            'dni',
            'fecha_nacimiento',
            'email',
            'password1',
            'password2'
        ]
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "dni": "DNI",
            "fecha_nacimiento": "Fecha de Nacimiento",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        # Recibimos el rol desde la vista
        self.rol = kwargs.pop('rol', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            user = User.objects.get(email=email)
            # Verificamos si ya tiene un perfil con este rol
            if Profile.objects.filter(user=user, rol=self.rol).exists():
                raise forms.ValidationError("Este correo electrónico ya tiene un perfil con ese rol.")
        except User.DoesNotExist:
            pass  # No hay problema, lo podrá registrar

        return email

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Las contraseñas no son iguales.')
        return cd['password2']

    def save(self, commit=True):
        email = self.cleaned_data['email']

        # Reutilizamos el usuario si ya existe
        try:
            user = User.objects.get(email=email)
            # No cambiamos la contraseña si el usuario ya existía
        except User.DoesNotExist:
            user = User(
                username=email,
                email=email,
            )
            user.set_password(self.cleaned_data['password1'])
            if commit:
                user.save()

        # Crear el perfil asociado (ya sea en flujo completo o reducido)
        profile = Profile(
            user=user,
            nombre=self.cleaned_data.get('nombre', ''),
            apellido=self.cleaned_data.get('apellido', ''),
            dni=self.cleaned_data.get('dni', ''),
            fecha_nacimiento=self.cleaned_data.get('fecha_nacimiento', None),
            email=email,
            rol=self.rol or 'general'
        )
        if commit:
            profile.save()

        return user, profile