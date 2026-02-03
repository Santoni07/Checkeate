from django import forms
from django.db import models
from Medico.models import Medico
from .models import (
    AptoGeneral,
    AntecedenteAptoGeneral,
    EstudiosAptoGeneral,
    ExamenFisicoGeneral,
    ExamenCardiovascularGeneral,
    ExamenRespiratorioGeneral,
    ExamenAbdomenGeneral,
    ExamenGenitourinarioGeneral,
    ExamenSomaGeneral,
    MotivoActividadGeneral,
)
from datetime import date

# ==============================
# Apto General
# ==============================
class AptoGeneralForm(forms.ModelForm):
    class Meta:
        model = AptoGeneral
        fields = ["estado", "fecha_caducidad", "observacion", "consentimiento_persona", "medico"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-select"}),
            "fecha_caducidad": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observacion": forms.TextInput(attrs={"class": "form-control"}),
            "consentimiento_persona": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "medico": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        medico = kwargs.pop("medico", None)
        super().__init__(*args, **kwargs)

        # 🔹 Aceptar distintos formatos (para evitar errores por localización)
        self.fields["fecha_caducidad"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]

        if medico:
            self.fields["medico"].queryset = Medico.objects.filter(id=medico.id)
            self.fields["medico"].initial = medico

    def clean_fecha_caducidad(self):
        fecha = self.cleaned_data.get("fecha_caducidad")
        if fecha and fecha < date.today():
            raise forms.ValidationError("⚠️ La fecha de caducidad no puede ser anterior al día de hoy.")
        return fecha

# ==============================
# Antecedentes
# ==============================

class AntecedenteAptoGeneralForm(forms.ModelForm):
    class Meta:
        model = AntecedenteAptoGeneral
        fields = [
            "fue_operado", "toma_medicacion", "estuvo_internado", "sufre_hormigueos",
            "es_diabetico", "es_asmatico", "es_alergico", "alerg_observ",
            "antecedente_epilepsia", "desviacion_columna", "dolor_cintura", "fracturas",
            "dolores_articulares", "falta_aire", "traumatismos_craneo", "dolor_pecho",
            "perdida_conocimiento", "presion_arterial", "muerte_subita_familiar",
            "enfermedad_cardiaca_familiar", "soplo_cardiaco", "abstenerse_competencia",
            "antecedentes_coronarios_familiares", "fumar_hipertension_diabetes",
            "fhd_observacion", "consumo_cocaina_anabolicos", "cca_observaciones",
            "vacunacion"
        ]

        labels = {
            "fue_operado": "¿Usted fue sometido a alguna cirugía?",
            "toma_medicacion": "¿Actualmente toma medicación de forma regular?",
            "estuvo_internado": "¿Estuvo internado en el último año?",
            "sufre_hormigueos": "¿Presenta hormigueos o pérdida de sensibilidad?",
            "es_diabetico": "¿Tiene diagnóstico de diabetes?",
            "es_asmatico": "¿Padece asma?",
            "es_alergico": "¿Tiene algún tipo de alergia?",
            "alerg_observ": "Observaciones sobre sus alergias",
            "antecedente_epilepsia": "¿Tiene antecedentes de epilepsia?",
            "desviacion_columna": "¿Le han diagnosticado desviación de columna?",
            "dolor_cintura": "¿Sufre dolores de cintura frecuentes?",
            "fracturas": "¿Ha tenido fracturas óseas?",
            "dolores_articulares": "¿Presenta dolores articulares?",
            "falta_aire": "¿Siente falta de aire en reposo o esfuerzo?",
            "traumatismos_craneo": "¿Ha sufrido traumatismos de cráneo?",
            "dolor_pecho": "¿Siente dolor en el pecho con frecuencia?",
            "perdida_conocimiento": "¿Ha tenido episodios de pérdida de conocimiento?",
            "presion_arterial": "¿Tiene antecedentes de presión arterial elevada?",
            "muerte_subita_familiar": "¿Hubo muerte súbita en su familia?",
            "enfermedad_cardiaca_familiar": "¿Tiene familiares con enfermedades cardíacas?",
            "soplo_cardiaco": "¿Le diagnosticaron soplo cardíaco?",
            "abstenerse_competencia": "¿Alguna vez le recomendaron abstenerse de competir?",
            "antecedentes_coronarios_familiares": "¿Existen antecedentes coronarios en su familia?",
            "fumar_hipertension_diabetes": "¿Fuma o tiene hipertensión/diabetes?",
            "fhd_observacion": "Observaciones adicionales sobre tabaquismo, HTA o diabetes",
            "consumo_cocaina_anabolicos": "¿Consume cocaína o anabólicos?",
            "cca_observaciones": "Observaciones sobre consumo de sustancias",
            "vacunacion": "¿Tiene el esquema de vacunación completo?",
        }

        widgets = {
            field: forms.CheckboxInput(attrs={"class": "form-check-input"})
            for field in fields if field not in ["alerg_observ", "fhd_observacion", "cca_observaciones"]
        }
        widgets.update({
            "alerg_observ": forms.TextInput(attrs={"class": "form-control", "placeholder": "Detalle sus alergias"}),
            "fhd_observacion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Detalle sobre tabaquismo, HTA o diabetes"}),
            "cca_observaciones": forms.TextInput(attrs={"class": "form-control", "placeholder": "Detalle sobre consumo de sustancias"}),
        })
class EstudioAptoGeneralForm(forms.ModelForm):
    class Meta:
        model = EstudiosAptoGeneral
        # apto se setea en la vista, fecha_creacion es auto por default
        fields = ['tipo_estudio', 'archivo', 'observaciones']
        widgets = {
            'tipo_estudio': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'}),
            'observaciones': forms.Textarea(attrs={
    'class': 'form-control',
    'rows': 3
}),


        }
# ==============================
# Examen Físico
# ==============================
class ExamenFisicoGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenFisicoGeneral
        fields = ["peso", "altura", "imc", "perimetro_cintura", "diagnostico"]
        widgets = {
            "peso": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.1",         # permite decimales
                "placeholder": "Ej: 70.5",
                "min": "0"
            }),
            "altura": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",        # admite altura con dos decimales
                "placeholder": "Ej: 1.75",
                "min": "0"
            }),
            "imc": forms.NumberInput(attrs={
                "class": "form-control",
                "readonly": "readonly",
                "placeholder": "Se calcula automáticamente"
            }),
            "perimetro_cintura": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.1",
                "placeholder": "Ej: 82.5"
            }),
            "diagnostico": forms.Select(attrs={
                "class": "form-select"
            }),
        }

# ==============================
# Examen Cardiovascular
# ==============================
class ExamenCardiovascularGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenCardiovascularGeneral
        fields = ["auscultacion", "ta1", "ta2", "pulso", "ecg"]
        widgets = {
            "auscultacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "ta1": forms.TextInput(attrs={"class": "form-control"}),
            "ta2": forms.TextInput(attrs={"class": "form-control"}),
            "pulso": forms.TextInput(attrs={"class": "form-control"}),
            "ecg": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ==============================
# Examen Respiratorio
# ==============================
class ExamenRespiratorioGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenRespiratorioGeneral
        fields = ["murmullo_vesicular", "ruidos_agregados", "saturacion_o2"]
        widgets = {
            "murmullo_vesicular": forms.TextInput(attrs={"class": "form-control"}),
            "ruidos_agregados": forms.TextInput(attrs={"class": "form-control"}),
            "saturacion_o2": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
        }


# ==============================
# Examen Abdomen
# ==============================
class ExamenAbdomenGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenAbdomenGeneral
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ==============================
# Examen Genitourinario
# ==============================
class ExamenGenitourinarioGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenGenitourinarioGeneral
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ==============================
# Examen Soma
# ==============================
class ExamenSomaGeneralForm(forms.ModelForm):
    class Meta:
        model = ExamenSomaGeneral
        fields = ["observacion"]
        widgets = {
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ==============================
# Motivo Actividad
# ==============================
class MotivoActividadGeneralForm(forms.ModelForm):
    class Meta:
        model = MotivoActividadGeneral
        fields = ["competitivo", "recreativo", "por_salud", "salud_detalle", "por_lesion", "lesion_detalle"]
        widgets = {
            "competitivo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "recreativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "por_salud": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "salud_detalle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Completa si seleccionaste 'Por salud'"
                }
            ),
            "por_lesion": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "lesion_detalle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Completa si seleccionaste 'Por lesión'"
                }
            ),
        }

