from django import forms
from .models import Persona, Jugador, Torneo, Categoria, Equipo, CategoriaEquipo, JugadorCategoriaEquipo,ActividadGeneral, JugadorActividadGeneral
from django.contrib.auth.forms import PasswordChangeForm



class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona

        fields = [ 'direccion', 'telefono', 'telefono_alternativo']
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer opcional el campo teléfono alternativo
        self.fields['telefono_alternativo'].required = False
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.telefono_alternativo:
            instance.telefono_alternativo = 'S/D'
        if commit:
            instance.save()
        return instance



class JugadorForm(forms.ModelForm):
    class Meta:
        model = Jugador
        fields = [ 'grupo_sanguineo', 'cobertura_medica', 'numero_afiliado']
        widgets = {
            'cobertura_medica': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_afiliado': forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer opcionales los campos de cobertura médica y número de afiliado
        self.fields['cobertura_medica'].required = False
        self.fields['numero_afiliado'].required = False
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.cobertura_medica:
            instance.cobertura_medica = 'S/D'
        if not instance.numero_afiliado:
            instance.numero_afiliado = 'S/D'
        if commit:
            instance.save()
        return instance


class TorneoForm(forms.ModelForm):
    class Meta:
        model = Torneo
        fields = ['nombre', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'torneo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'torneo': forms.Select(attrs={'class': 'form-control'}),
        }

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CategoriaEquipoForm(forms.ModelForm):
    class Meta:
        model = CategoriaEquipo
        fields = ['categoria', 'equipo']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'equipo': forms.Select(attrs={'class': 'form-control'}),
        }

class JugadorCategoriaEquipoForm(forms.ModelForm):
    class Meta:
        model = JugadorCategoriaEquipo
        fields = ['jugador', 'categoria_equipo']
        widgets = {
            'jugador': forms.Select(attrs={'class': 'form-control'}),
            'categoria_equipo': forms.Select(attrs={'class': 'form-control'}),
        }


class ActividadGeneralForm(forms.ModelForm):
    class Meta:
        model = ActividadGeneral
        fields = ["nombre", "descripcion", "direccion", "telefono", "imagen", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class JugadorActividadGeneralForm(forms.ModelForm):
    class Meta:
        model = JugadorActividadGeneral
        fields = ["jugador", "actividad"]
        widgets = {
            "jugador": forms.Select(attrs={"class": "form-select"}),
            "actividad": forms.Select(attrs={"class": "form-select"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True
    )
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("La contraseña actual no es correcta.")
        return old_password