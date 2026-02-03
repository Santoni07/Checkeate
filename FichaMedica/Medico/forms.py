from django import forms
from .models import Medico, Documentos


class DocumentosForm(forms.ModelForm):
    class Meta:
        model = Documentos
        fields = ['certificado_matricula', 'certificado_firma_electronica', 'contrato_aceptado']
        widgets = {
            'contrato_aceptado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class MedicoDatosComplementariosForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['matricula', 'especialidad', 'direccion', 'telefono_consultorio']
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 123456'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cardiología'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Siempre Viva 123'}),
            'telefono_consultorio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 351-1234567'}),
        }

from .models import ObservacionPersona


class ObservacionPersonaForm(forms.ModelForm):
    class Meta:
        model = ObservacionPersona
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escriba una observación..."
            })
        }