from django import forms
from django.core.exceptions import ValidationError

from .models import AptoExterno
from .services import convertir_a_pdf


from Representate.models import RepresentanteActividadGeneral



class AptoExternoForm(forms.ModelForm):

    class Meta:
        model = AptoExterno
        fields = [

            "actividad",
            "torneo",
            "competencia",
            "archivo_pdf",
            "fecha_emision",
            "fecha_vencimiento",
            "observaciones",
        ]

        widgets = {
            "fecha_emision": forms.DateInput(attrs={"type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Observaciones administrativas (opcional)",
                "class": "form-control",
            }),
        }

    # ===============================
    # 🔐 FILTRAR ACTIVIDAD POR PERFIL
    # ===============================
    def __init__(self, *args, **kwargs):
        profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)

        if profile:
            try:
                rel = RepresentanteActividadGeneral.objects.get(profile=profile)

                # 👉 solo la actividad del representante
                self.fields["actividad"].queryset = (
                    self.fields["actividad"]
                    .queryset
                    .filter(id=rel.actividad.id)
                )

                # 👉 preseleccionada (UX)
                self.fields["actividad"].initial = rel.actividad

            except RepresentanteActividadGeneral.DoesNotExist:
                # si no tiene actividad, no mostramos nada
                self.fields["actividad"].queryset = self.fields["actividad"].queryset.none()

    # ===============================
    # 🔄 CONVERSIÓN IMAGEN → PDF
    # ===============================
    def clean_archivo_pdf(self):
        archivo = self.cleaned_data.get("archivo_pdf")

        if not archivo:
            return archivo

        extension = archivo.name.lower().split(".")[-1]

        # 📄 Si ya es PDF → no hacer nada
        if extension == "pdf":
            return archivo

        # 🖼️ Si es imagen → convertir
        if extension in ["jpg", "jpeg", "png"]:
            return convertir_a_pdf(archivo)

        raise ValidationError(
            "Formato no permitido. Solo JPG, PNG o PDF."
        )

    # ===============================
    # 🧠 REGLAS DE NEGOCIO
    # ===============================
    def clean(self):
        cleaned_data = super().clean()

        actividad = cleaned_data.get("actividad")
        torneo = cleaned_data.get("torneo")
        competencia = cleaned_data.get("competencia")

        if actividad and torneo:
            raise ValidationError(
                "Debe asignar el apto a una actividad O a un torneo, no a ambos."
            )

        if competencia and not torneo:
            raise ValidationError(
                "No puede asignar una competencia sin un torneo."
            )

        return cleaned_data
