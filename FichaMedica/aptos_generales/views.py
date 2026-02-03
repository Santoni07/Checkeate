from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import AptoGeneral, AntecedenteAptoGeneral, EstudiosAptoGeneral
from RegistroMedico.models import AntecedenteEnfermedades
from .forms import AntecedenteAptoGeneralForm
from django.forms.models import model_to_dict
from persona.models import *

from django.contrib.auth.decorators import login_required

from account.models import Profile
from persona.utils import get_persona_from_user


# Crear (con precarga si hay antecedentes base)

def antecedentes_home(request):
    # 1) tomar el profile actual desde sesión
    profile_id = request.session.get("user_profile_id")
    print(f"[antecedentes_home] profile_id={profile_id}")
    if not profile_id:
        messages.error(request, "Sesión inválida. Iniciá sesión nuevamente.")
        return redirect("login")

    # 2) persona del profile
    persona = get_persona_from_user(request.user)
    print(f"[antecedentes_home] persona={persona}")
    if not persona:
        messages.warning(request, "Primero completá tus datos personales.")
        return redirect("registrar_persona")

    # 3) jugador de esa persona
    jugador = Jugador.objects.filter(persona=persona).first()
    print(f"[antecedentes_home] jugador={jugador}")
    if not jugador:
        messages.warning(request, "Necesitás completar el registro de jugador.")
        return redirect("registrar_persona")

    # 4) apto más reciente del jugador
    apto = AptoGeneral.objects.filter(jugador=jugador).order_by("-fecha_creacion").first()
    print(f"[antecedentes_home] apto={apto}")
    if not apto:
        messages.info(request, "Aún no tenés un Apto General. Inscribite en una actividad para generarlo.")
        return redirect("menu_jugador")

    # 5) redirigir a la vista que lista/visualiza los antecedentes de ese apto
    return redirect("aptos_generales:antecedentes_list", apto_id=apto.id)
# Crear (con precarga si hay antecedentes base)
def antecedentes_create(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    jugador = apto.jugador

    # ⚡ Si ya existe → redirigir a update
    if AntecedenteAptoGeneral.objects.filter(apto=apto).exists():
        return redirect("aptos_generales:antecedentes_update", apto_id=apto.id)

    # Precarga desde AntecedenteEnfermedades
    try:
        antecedentes_base = AntecedenteEnfermedades.objects.get(jugador=jugador)
        initial_data = {
            field.name: getattr(antecedentes_base, field.name)
            for field in antecedentes_base._meta.fields
            if field.name not in ["id", "jugador"]
        }
    except AntecedenteEnfermedades.DoesNotExist:
        initial_data = {}

    if request.method == "POST":
        form = AntecedenteAptoGeneralForm(request.POST)
        if form.is_valid():
            antecedente = form.save(commit=False)
            antecedente.apto = apto
            antecedente.jugador = jugador
            antecedente.save()
            messages.success(request, "Antecedentes cargados correctamente.")
            return redirect("aptos_generales:antecedentes_list", apto_id=apto.id)
    else:
        form = AntecedenteAptoGeneralForm(initial=initial_data)

    return render(request, "aptos_generales/antecedentes_form.html", {
        "form": form,
        "apto": apto,
        "is_update": False
    })


# Actualizar
def antecedentes_update(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    jugador = apto.jugador

    # Si no existe, lo creo y lo inicializo con los antecedentes base del jugador
    antecedentes_base = None
    try:
        antecedentes_base = AntecedenteEnfermedades.objects.get(jugador=jugador)
    except AntecedenteEnfermedades.DoesNotExist:
        pass

    antecedente, created = AntecedenteAptoGeneral.objects.get_or_create(
        apto=apto,
        jugador=jugador,
        defaults={
            field.name: getattr(antecedentes_base, field.name)
            for field in antecedentes_base._meta.fields
            if antecedentes_base and field.name not in ["id", "jugador", "apto"]
        } if antecedentes_base else {}
    )

    if request.method == "POST":
        form = AntecedenteAptoGeneralForm(request.POST, instance=antecedente)
        if form.is_valid():
            form.save()
            messages.success(request, "Antecedentes actualizados correctamente.")
            return redirect("aptos_generales:antecedentes_list", apto_id=apto.id)
    else:
        form = AntecedenteAptoGeneralForm(instance=antecedente)

    return render(request, "aptos_generales/antecedentes_form.html", {
        "form": form,
        "apto": apto,
        "is_update": True
    })

# Listar
def antecedentes_list(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    antecedentes = AntecedenteAptoGeneral.objects.filter(apto=apto)
    return render(request, "aptos_generales/antecedentes_list.html", {"apto": apto, "antecedentes": antecedentes})


# Eliminar
def antecedentes_delete(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    antecedente = get_object_or_404(AntecedenteAptoGeneral, apto=apto)

    if request.method == "POST":
        antecedente.delete()
        messages.success(request, "Antecedentes eliminados correctamente.")
        return redirect("antecedentes_list", apto_id=apto.id)

    return render(request, "aptos_generales/antecedentes_confirm_delete.html", {"apto": apto, "antecedente": antecedente})


def antecedentes_detail(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    antecedente = get_object_or_404(AntecedenteAptoGeneral, apto=apto)
    return render(request, "aptos_generales/antecedentes_detail.html", {
        "apto": apto,
        "antecedente": antecedente
    })


@login_required
def antecedentes_select(request):
    profile_id = request.session.get("user_profile_id")
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)

    # Todos los aptos del jugador
    aptos = AptoGeneral.objects.filter(jugador=jugador).order_by("-fecha_creacion")

    # ✅ SOLO antecedentes completos
    aptos_completos = []
    for apto in aptos:
        snap = apto.antecedentes_snapshot
        if snap and snap.esta_completo():
            aptos_completos.append(apto)

    return render(request, "aptos_generales/antecedentes_select.html", {
        "aptos": aptos_completos,
        "jugador": jugador,
        "persona": persona,
        "profile": profile,
    })

@login_required
def ver_estudios_jugador(request):
    # Traer el perfil en sesión
    profile_id = request.session.get("user_profile_id")
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    # Obtener el jugador
    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)

    # 🔽 Traer todos los estudios de todos los aptos de este jugador
    estudios = (
        EstudiosAptoGeneral.objects
        .filter(apto__jugador=jugador)
        .select_related("apto")
        .order_by("-fecha_creacion")   # más recientes primero
    )

    return render(request, "aptos_generales/ver_estudios_jugador.html", {
        "jugador": jugador,
        "estudios": estudios,
    })