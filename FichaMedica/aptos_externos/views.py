from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from persona.models import Persona
from .forms import AptoExternoForm
from Representate.models import RepresentanteActividadGeneral
from .models import AptoExterno
from django.core.exceptions import ObjectDoesNotExist
from account.models import Profile



@login_required
def cargar_apto_externo(request):
    """
    Flujo:
    1) Buscar persona por DNI
    2) Si existe, mostrar form para cargar apto externo
    """

    dni = request.GET.get("dni")
    persona = None
    form = None

    # 🔐 Obtener profile correctamente
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Error de perfil. Contacte al administrador.")
        return redirect("home")  # o donde corresponda

    # 🔍 Buscar persona por DNI
    if dni:
        persona = (
            Persona.objects
            .filter(profile__dni=dni)
            .select_related("profile")
            .first()
        )

        if not persona:
            messages.warning(
                request,
                "⚠️ No se encontró ningún paciente con ese DNI."
            )

    # 📄 Si hay persona, permitir carga del apto
    if persona:
        if request.method == "POST":
            form = AptoExternoForm(
                request.POST,
                request.FILES,
                profile=profile
            )

            if form.is_valid():
                apto = form.save(commit=False)
                apto.persona = persona
                apto.representante = profile
                apto.save()

                messages.success(
                    request,
                    "✅ El apto externo se cargó correctamente."
                )

                # ✅ REDIRECCIÓN CORRECTA
                return redirect("aptos_externos_listado_actividad")
            else:
                print(form.errors)
        else:
            form = AptoExternoForm(profile=profile)

    # 👉 Render NORMAL de carga
    return render(
        request,
        "aptos_externos/cargar.html",
        {
            "persona": persona,
            "dni": dni,
            "form": form,
        }
    )
@login_required
def listado_aptos_externos_por_actividad(request):
    from django.utils import timezone

    today = timezone.now().date()
    estado = request.GET.get("estado")
    dni = request.GET.get("dni")

    try:
        profile = Profile.objects.get(user=request.user)
        representante_actividad = (
            RepresentanteActividadGeneral.objects
            .select_related("actividad")
            .get(profile=profile)
        )
    except (Profile.DoesNotExist, RepresentanteActividadGeneral.DoesNotExist):
        return render(
            request,
            "aptos_externos/listado.html",
            {
                "aptos": [],
                "error": "El representante no tiene una actividad asignada.",
            }
        )

    actividad = representante_actividad.actividad

    # 🔹 Queryset base (actividad)
    aptos_base = (
        AptoExterno.objects
        .filter(actividad=actividad, activo=True)
        .select_related("persona__profile")
    )

    # 🔍 FILTRO POR DNI (si existe)
    if dni:
        aptos_base = aptos_base.filter(persona__profile__dni=dni)

    # 🔢 CONTADORES (siempre sobre base SIN estado)
    total_count = aptos_base.count()
    vigentes_count = aptos_base.filter(fecha_vencimiento__gte=today).count()
    vencidos_count = aptos_base.filter(fecha_vencimiento__lt=today).count()

    # 🚦 FILTRO POR ESTADO
    aptos = aptos_base
    if estado == "VIGENTE":
        aptos = aptos.filter(fecha_vencimiento__gte=today)
    elif estado == "VENCIDO":
        aptos = aptos.filter(fecha_vencimiento__lt=today)

    # ❗️Si no hay dni ni estado → NO mostrar nada
    if not dni and not estado:
        aptos = AptoExterno.objects.none()

    return render(
        request,
        "aptos_externos/listado.html",
        {
            "aptos": aptos,
            "actividad": actividad,
            "today": today,
            "dni": dni,
            "estado": estado,
            "total_count": total_count,
            "vigentes_count": vigentes_count,
            "vencidos_count": vencidos_count,
        }
    )