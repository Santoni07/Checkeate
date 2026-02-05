
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from Medico.models import Medico
from RegistroMedico.models import AntecedenteEnfermedades, RegistroMedico
from account.models import Profile
from persona.models import Persona, Jugador
from aptos_generales.models import AptoGeneral, AntecedenteAptoGeneral,ActividadGeneral
from datetime import timedelta
from django.utils import timezone
from .forms import *
from .models import *
from django.db import transaction
from django.db.models import Q
from .models import Torneo, Competencia, ActividadGeneral
import json
from persona.utils import get_persona_from_user


@login_required
def registrar_persona(request):
    persona = get_persona_from_user(request.user)

    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id, user=request.user).first()

    if not profile:
        messages.error(request, "No se pudo identificar tu perfil.")
        return redirect("select_role")

    jugador = Jugador.objects.filter(persona=persona).first()

    if request.method == "POST":
        form_persona = PersonaForm(request.POST, instance=persona)
        form_jugador = JugadorForm(request.POST, instance=jugador)

        if form_persona.is_valid() and form_jugador.is_valid():
            persona = form_persona.save(commit=False)
            persona.user = request.user
            persona.profile = profile      # 🔥 FIX CLAVE
            persona.save()

            jugador = form_jugador.save(commit=False)
            jugador.persona = persona
            jugador.save()

            messages.success(request, "¡Datos guardados correctamente!")

            if profile.rol == "paciente":
                return redirect("menu_paciente")
            else:
                return redirect("seleccionar_categoria_equipo")
        else:
            messages.error(request, "Por favor, corregí los errores en el formulario.")
    else:
        form_persona = PersonaForm(instance=persona)
        form_jugador = JugadorForm(instance=jugador)

    return render(request, "persona/registrar_persona.html", {
        "form_persona": form_persona,
        "form_jugador": form_jugador,
        "persona": persona,
        "profile": profile,
        "jugador": jugador,
    })




def fetch_categorias(request, torneo_id):
    try:
        print(f"Torneo seleccionado: {torneo_id}")
        categorias = Categoria.objects.filter(torneo_id=torneo_id).values('id', 'nombre')
        print(categorias)  # Para verificar qué categorías se obtienen
        return JsonResponse({'categorias': list(categorias)})
    except Exception as e:
        print(f"Error al obtener categorías: {e}")  # Para ver cualquier error
        return JsonResponse({'error': str(e)}, status=500)


def fetch_equipos(request, categoria_id):
    # Filtrar los equipos relacionados con la categoría especificada
    try:
        equipos = Equipo.objects.filter(categoria_equipos__categoria_id=categoria_id).values('id', 'nombre')
        print(equipos)
        return JsonResponse({'equipos': list(equipos)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


    print(f"Torneo seleccionado:")
    if request.method == 'POST':
        # Solicitud POST: Procesar el formulario
        print("Solicitud POST recibida")
        print(request.POST)
        torneo_id = request.POST.get('torneo')
        print(f"Torneo seleccionado: {torneo_id}")
        categoria_id = request.POST.get('categoria')
        equipo_id = request.POST.get('equipo')

        # Obtener la persona y el jugador
        persona = get_object_or_404(Persona, profile=request.user.profile)
        jugador = Jugador.objects.get(persona=persona)

        # Obtener la instancia de CategoriaEquipo
        categoria_equipo = get_object_or_404(CategoriaEquipo, categoria_id=categoria_id, equipo_id=equipo_id)

        # Crear la asociación en el modelo JugadorCategoriaEquipo
        JugadorCategoriaEquipo.objects.create(
            jugador=jugador,
            categoria_equipo=categoria_equipo  # Cambiado a la instancia de CategoriaEquipo
        )

        # Redirigir o mostrar un mensaje de éxito
        return redirect('registro_exitoso')  # O la URL a la que quieras redirigir

    else:
        # Solicitud GET: Cargar torneos y renderizar el formulario
        torneos = Torneo.objects.all()
        print(torneos)
        return render(request, 'persona/seleccionar_categoria_equipo.html', {'torneos': torneos})


@login_required
@transaction.atomic
def seleccionar_categoria_equipo(request):
    """Permite inscribirse a un TORNEO (torneo+categoria+equipo) o a una COMPETENCIA (solo competencia).
       Crea el RegistroMedico según corresponda y la relación JugadorCategoriaEquipo si elige torneo.
    """
    # --- Identidad del usuario/jugador ---
    profile_id = request.session.get("user_profile_id")
    profile = get_object_or_404(Profile, id=profile_id)
    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)

    if request.method == 'POST':
        tipo = request.POST.get('tipo_evento')  # 'torneo' o 'competencia'

        if tipo == 'torneo':
            torneo_id = request.POST.get('torneo')
            categoria_id = request.POST.get('categoria')
            equipo_id = request.POST.get('equipo')

            if not (torneo_id and categoria_id and equipo_id):
                messages.error(request, "Seleccioná torneo, categoría y equipo.")
                return redirect('seleccionar_categoria_equipo')

            # Validaciones de existencia
            torneo = get_object_or_404(Torneo, id=torneo_id)
            categoria_equipo = get_object_or_404(CategoriaEquipo, categoria_id=categoria_id, equipo_id=equipo_id)

            # Crear relación Jugador–CategoriaEquipo si no existe
            if not JugadorCategoriaEquipo.objects.filter(jugador=jugador, categoria_equipo=categoria_equipo).exists():
                JugadorCategoriaEquipo.objects.create(jugador=jugador, categoria_equipo=categoria_equipo)

            # Crear ficha (RegistroMedico) para torneo (competencia null)
            RegistroMedico.objects.create(
                jugador=jugador,
                torneo=torneo,
                competencia=None,
                estado='PROCESO'
            )
            messages.success(request, "¡Inscripción al torneo registrada!")
            return redirect('menu_jugador')

        elif tipo == 'competencia':
            competencia_id = request.POST.get('competencia')
            if not competencia_id:
                messages.error(request, "Seleccioná una competencia.")
                return redirect('seleccionar_categoria_equipo')

            competencia = get_object_or_404(Competencia, id=competencia_id)

            # Crear ficha (RegistroMedico) para competencia (torneo null)
            RegistroMedico.objects.create(
                jugador=jugador,
                torneo=None,
                competencia=competencia,
                estado='PROCESO'
            )
            messages.success(request, "¡Inscripción a la competencia registrada!")
            return redirect('menu_jugador')

        else:
            messages.error(request, "Seleccioná si es Torneo o Competencia.")
            return redirect('seleccionar_categoria_equipo')

    # --- GET: armo contexto seguro, sin suponer relaciones previas ---
    torneos = Torneo.objects.all().order_by('nombre')
    competencias = Competencia.objects.all().order_by('nombre')

    # Si querés preseleccionar algo si ya había relación, hacelo de forma segura:
    jce = JugadorCategoriaEquipo.objects.filter(jugador=jugador).select_related('categoria_equipo').first()
    pre_categoria_id = jce.categoria_equipo.categoria_id if jce else None
    pre_equipo_id = jce.categoria_equipo.equipo_id if jce else None

    return render(request, 'persona/seleccionar_categoria_equipo.html', {
        'torneos': torneos,
        'competencias': competencias,
        'pre_categoria_id': pre_categoria_id,
        'pre_equipo_id': pre_equipo_id,
    })

def error_registro(request):
    return render(request, 'persona/error_registro.html')



@login_required
@never_cache
def menu_jugador(request):
    # =========================
    # MÉDICOS
    # =========================
    medicos = Medico.objects.select_related('profile').all()

    # =========================
    # PERFIL / PERSONA / JUGADOR
    # =========================
    try:
        profile = Profile.objects.get(user=request.user, rol='jugador')
    except Profile.DoesNotExist:
        return redirect('select_role')

    try:
        persona = get_persona_from_user(request.user)
        jugador = Jugador.objects.get(persona=persona)
    except (Persona.DoesNotExist, Jugador.DoesNotExist):
        return redirect('registrar_persona')

   # =========================
# CONTROL DE FLUJO JUGADOR
# =========================

    # 1️⃣ Primera vez: nunca se inscribió a torneo / competencia
    if not RegistroMedico.objects.filter(jugador=jugador).exists():
        return redirect('inscribirse_a_torneo')

    # 2️⃣ Tiene ficha en PROCESO
    ficha_pendiente = RegistroMedico.objects.filter(
        jugador=jugador,
        estado='PROCESO'
    ).first()

    if ficha_pendiente:
        # 2.a → no tiene antecedentes cargados
        antecedentes = AntecedenteEnfermedades.objects.filter(jugador=jugador).first()
        if not antecedentes:
            return redirect(
                'registroMedico:cargar_antecedente',
                jugador_id=jugador.id
            )

        # 2.b → tiene antecedentes pero falta consentimiento
        if not ficha_pendiente.consentimiento_persona:
            return redirect(
                'registroMedico:consentimiento',
                pk=ficha_pendiente.id
            )
    # =========================
    # TODAS LAS FICHAS DEL JUGADOR
    # =========================
    fichas_qs = (
        RegistroMedico.objects
        .filter(jugador=jugador)
        .select_related('torneo', 'competencia')
        .order_by('-id')
    )

    fichas_medicas_data = list(fichas_qs)
    ficha_medica_primera = fichas_qs.first()

    # =========================
    # ANTECEDENTES (OneToOne)
    # =========================
    antecedentes = AntecedenteEnfermedades.objects.filter(jugador=jugador).first()

    # =========================
    # CONSENTIMIENTO PENDIENTE
    # =========================
    mostrar_consentimiento_pendiente = False
    ficha_sin_consentimiento = None

    for f in fichas_medicas_data:
        if not f.consentimiento_persona:
            mostrar_consentimiento_pendiente = True
            ficha_sin_consentimiento = f
            break

    # =========================
    # TABLA DE TORNEOS
    # =========================
    jugador_categoria_equipos = (
        JugadorCategoriaEquipo.objects
        .select_related(
            'categoria_equipo__categoria__torneo',
            'categoria_equipo__equipo'
        )
        .filter(jugador=jugador)
    )

    jugador_info = {
        'nombre': jugador.persona.profile.nombre,
        'apellido': jugador.persona.profile.apellido,
        'direccion': jugador.persona.direccion,
        'telefono': jugador.persona.telefono,
        'grupo_sanguineo': jugador.grupo_sanguineo,
        'cobertura_medica': jugador.cobertura_medica,
        'numero_afiliado': jugador.numero_afiliado,
        'categorias_equipo': []
    }

    for jc in jugador_categoria_equipos:
        ce = jc.categoria_equipo
        torneo = ce.categoria.torneo

        ficha_medica_asociada = fichas_qs.filter(torneo=torneo).first()

        jugador_info['categorias_equipo'].append({
            'nombre_categoria': ce.categoria.nombre,
            'nombre_equipo': ce.equipo.nombre,
            'torneo': {
                'nombre': torneo.nombre,
                'descripcion': getattr(torneo, 'descripcion', '') or "—",
                'direccion': getattr(torneo, 'direccion', '') or "—",
                'telefono': getattr(torneo, 'telefono', '') or "—",
                'imagen': torneo.imagen.url if getattr(torneo, 'imagen', None) else None,
            },
            'ficha_medica': ficha_medica_asociada,
        })

    # =========================
    # TABLA DE COMPETENCIAS
    # =========================
    fichas_competencias = [f for f in fichas_medicas_data if f.competencia_id]
    competencias_info = []

    for rm in fichas_competencias:
        comp = rm.competencia
        competencias_info.append({
            'competencia': {
                'nombre': comp.nombre,
            },
            'ficha_medica': rm,
        })

    # =========================
    # CONTEXTO
    # =========================
    context = {
        'persona': persona,
        'profile': profile,
        'jugador': jugador,
        'jugador_id': jugador.id,

        # torneos (con categoría / equipo)
        'jugador_info': jugador_info,

        # competencias
        'competencias_info': competencias_info,

        # banderas
        'show_torneo_table': bool(jugador_info['categorias_equipo']),
        'show_competencia_table': bool(competencias_info),

        # fichas / antecedentes
        'antecedentes': antecedentes,
        'ficha_medica': fichas_qs,
        'ficha_medica_data': fichas_medicas_data,
        'ficha_medica_primera': ficha_medica_primera,

        # médicos
        'medicos': medicos,

        # consentimiento
        'mostrar_consentimiento_pendiente': mostrar_consentimiento_pendiente,
        'ficha_sin_consentimiento': ficha_sin_consentimiento,
    }

    return render(request, 'persona/menu_jugador.html', context)

def medicos_inscriptos_view(request):

    # 1. Traemos médicos que tengan al menos matrícula y teléfono
    medicos_qs = (
        Medico.objects
        .select_related('profile')
        .filter(
            matricula__isnull=False
        ).exclude(matricula="")
        .filter(
            telefono_consultorio__isnull=False
        ).exclude(telefono_consultorio="")
        .filter(
            direccion__isnull=False
        ).exclude(direccion="")
    )

    # 2. Validamos campos del profile
    medicos_filtrados = []

    for medico in medicos_qs:
        p = medico.profile

        if (
            p and p.nombre and p.apellido and p.email
            and medico.especialidad  # especialidad no vacía
        ):
            medicos_filtrados.append(medico)

    return render(
        request,
        'persona/medicos_inscriptos.html',
        {'medicos': medicos_filtrados}
    )

@login_required
def modificar_perfil(request):
    # 🔹 Obtenemos el profile activo desde la sesión
    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()

    if not profile:
        return HttpResponse("No se pudo cargar el perfil.", status=404)

    # 🔹 Buscamos persona y jugador asociados

    persona = Persona.objects.filter(user=request.user).first()
    if not persona:
        persona = Persona.objects.create(
            user=request.user,
            telefono_alternativo="S/D"
        )
    jugador = Jugador.objects.filter(persona=persona).first()

    if request.method == 'POST':
        form_persona = PersonaForm(request.POST, instance=persona)
        form_jugador = JugadorForm(request.POST, instance=jugador)

        if form_persona.is_valid() and form_jugador.is_valid():
            # ✅ Guardamos Persona con su Profile asignado
            persona_obj = form_persona.save(commit=False)
            persona_obj.user = request.user   # 🔑 CLAVE
            persona_obj.save()

            # ✅ Guardamos Jugador con su Persona asignada
            jugador_obj = form_jugador.save(commit=False)
            jugador_obj.persona = persona_obj
            jugador_obj.save()

            messages.success(request, "¡Perfil actualizado correctamente!")
            return redirect('perfil')
        else:
            messages.error(request, "Por favor, corregí los errores en el formulario.")
    else:
        form_persona = PersonaForm(instance=persona)
        form_jugador = JugadorForm(instance=jugador)

    return render(request, 'persona/modificar_perfil.html', {
        'form_persona': form_persona,
        'form_jugador': form_jugador,
        'jugador': jugador,
        'profile': profile,
    })


@login_required
def perfil(request):
    # Obtener el perfil activo desde la sesión
    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()

    if not profile:
        return HttpResponse("No se pudo cargar el perfil.", status=404)

    # Obtener la persona asociada al perfil (si existe)
    persona = get_persona_from_user(request.user)

    # Obtener el jugador asociado a la persona (si existe)
    jugador = getattr(persona, 'jugador', None) if persona else None

    # Pasar profile, persona y jugador al contexto
    return render(request, 'persona/perfil.html', {
        'profile': profile,
        'persona': persona,
        'jugador': jugador,
    })

def cambiar_email(request):
    # Obtener el perfil del usuario actual
    profile = request.user.profile

    if request.method == 'POST':

        new_email = request.POST.get('email')


        user = request.user
        user.email = new_email


        user.username = new_email

        user.save()


        profile.email = new_email
        profile.save()

        return redirect('perfil')

    return render(request, 'persona/modificar_email.html', {'profile': profile})

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput,
        required=True
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        print("🔍 [DEBUG] Contraseña actual ingresada:", old_password)  # LOG
        if not self.user.check_password(old_password):
            print("❌ [DEBUG] Contraseña actual INCORRECTA")
            raise forms.ValidationError("La contraseña actual no es correcta.")
        print("✅ [DEBUG] Contraseña actual validada correctamente")
        return old_password

def cambiar_contraseña(request):
    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()

    if request.method == 'POST':
        print("📩 [DEBUG] POST recibido con data:", request.POST)  # LOG
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            print("✅ [DEBUG] Formulario válido")
            user = form.save()
            update_session_auth_hash(request, user)  # mantiene la sesión activa
            print("🔑 [DEBUG] Contraseña cambiada para usuario:", user.username)
            request.session['password_changed'] = True
            return redirect('modificar_contrasena')
        else:
            print("❌ [DEBUG] Errores en el formulario:", form.errors)
            messages.error(request, f"Errores en el formulario: {form.errors}")
    else:
        print("➡️ [DEBUG] GET - mostrando formulario vacío")
        form = CustomPasswordChangeForm(request.user)

    if request.session.get('password_changed'):
        print("🎉 [DEBUG] Contraseña cambiada con éxito (session flag detectado)")
        messages.success(request, '¡Contraseña cambiada con éxito!')
        del request.session['password_changed']

    return render(request, 'persona/modificar_contrasena.html', {
        'form': form,
        'profile': profile
    })

# funcion para inscribirme en un nuevo torneo


@login_required
def inscribirse_a_torneo(request):
    profile = get_object_or_404(Profile, user=request.user, rol='jugador')
    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)

    torneos_con_ficha_vigente_ids = RegistroMedico.objects.filter(
        jugador=jugador, torneo__isnull=False
    ).exclude(estado='VENCIDO').values_list('torneo_id', flat=True)

    competencias_con_ficha_vigente_ids = RegistroMedico.objects.filter(
        jugador=jugador, competencia__isnull=False
    ).exclude(estado='VENCIDO').values_list('competencia_id', flat=True)

    torneos_disponibles = Torneo.objects.exclude(id__in=torneos_con_ficha_vigente_ids)
    competencias_disponibles = Competencia.objects.exclude(id__in=competencias_con_ficha_vigente_ids)

    if request.method == 'POST':
        competencia_id = (request.POST.get('competencia_id') or '').strip()
        torneo_id = (request.POST.get('torneo_id') or '').strip()
        categoria_id = (request.POST.get('categoria_id') or '').strip()
        equipo_id = (request.POST.get('equipo_id') or '').strip()

        # ===== COMPETENCIA =====
        if competencia_id and not torneo_id:
            competencia = get_object_or_404(Competencia, id=competencia_id)

            ya_vigente = RegistroMedico.objects.filter(
                jugador=jugador, competencia=competencia
            ).exclude(estado='VENCIDO').exists()

            if ya_vigente:
                messages.info(request, 'Ya estás inscripto en esta competencia.')
                return redirect('menu_jugador')

            RegistroMedico.objects.create(
                jugador=jugador,
                competencia=competencia,
                estado='PROCESO',
                consentimiento_persona=False,
                observacion='Inscripción a competencia'
            )

            messages.success(
                request,
                'Te inscribiste a la competencia. Completá los antecedentes médicos.'
            )
            return redirect('menu_jugador')

        # ===== TORNEO =====
        if torneo_id and categoria_id and equipo_id and not competencia_id:
            torneo = get_object_or_404(Torneo, id=torneo_id)
            categoria = get_object_or_404(Categoria, id=categoria_id, torneo=torneo)
            equipo = get_object_or_404(Equipo, id=equipo_id)

            categoria_equipo, _ = CategoriaEquipo.objects.get_or_create(
                categoria=categoria, equipo=equipo
            )

            JugadorCategoriaEquipo.objects.get_or_create(
                jugador=jugador, categoria_equipo=categoria_equipo
            )

            ya_vigente = RegistroMedico.objects.filter(
                jugador=jugador, torneo=torneo
            ).exclude(estado='VENCIDO').exists()

            if ya_vigente:
                messages.info(request, 'Ya estás inscripto en este torneo.')
                return redirect('menu_jugador')

            RegistroMedico.objects.create(
                jugador=jugador,
                torneo=torneo,
                estado='PROCESO',
                consentimiento_persona=False,
                observacion='Inscripción a torneo'
            )

            messages.success(
                request,
                'Te inscribiste al torneo. Completá los antecedentes médicos.'
            )
            return redirect('menu_jugador')

        messages.error(request, 'Faltan datos para inscribirte.')
        return redirect('inscribirse_a_torneo')

    return render(request, 'persona/inscribirse_torneo.html', {
        'torneos_disponibles': torneos_disponibles,
        'competencias_disponibles': competencias_disponibles,
    })

@login_required
def menu_paciente(request):
    profile_id = request.session.get("user_profile_id")
    profile = get_object_or_404(Profile, id=profile_id, user=request.user)

    persona = get_persona_from_user(request.user)
    jugador = Jugador.objects.filter(persona=persona).first() if persona else None

    aptos = (
        AptoGeneral.objects.filter(jugador__persona=persona)
        .select_related("actividad", "medico")
        .order_by("-fecha_creacion")
        if jugador else AptoGeneral.objects.none()
    )

    apto_actual = None

    for apto in aptos:
        antecedentes = getattr(apto, "antecedentes_snapshot", None)
        if not antecedentes or not antecedentes.esta_completo():
            apto_actual = apto
            break

    # 🚀 REDIRECCIÓN AUTOMÁTICA AL FLUJO DE ANTECEDENTES
    if apto_actual:
        return redirect(
        "aptos_generales:antecedentes_update",
        apto_id=apto_actual.id
    )

    tiene_actividad = aptos.filter(actividad__isnull=False).exists()
    actividades = ActividadGeneral.objects.all()

    antecedentes_por_apto = {}
    for apto in aptos:
        antecedentes = getattr(apto, "antecedentes_snapshot", None)
        antecedentes_por_apto[apto.id] = (
            antecedentes.esta_completo() if antecedentes else False
        )

    antecedentes_json = json.dumps(antecedentes_por_apto)

    hay_antecedente_vacio = any(
        not getattr(apto, "antecedentes_snapshot", None) or
        not getattr(apto, "antecedentes_snapshot", None).esta_completo()
        for apto in aptos
    )

    hay_antecedente_completo = any(
        getattr(apto, "antecedentes_snapshot", None) and
        getattr(apto, "antecedentes_snapshot", None).esta_completo()
        for apto in aptos
    )

    context = {
        "profile": profile,
        "persona": persona,
        "jugador": jugador,
        "aptos": aptos,
        "tiene_actividad": tiene_actividad,
        "antecedentes_por_apto": antecedentes_json,
        "hay_antecedente_vacio": hay_antecedente_vacio,
        "hay_antecedente_completo": hay_antecedente_completo,
        "actividades": actividades,
    }

    return render(request, "persona/menu_paciente.html", context)



def listado_eventos_view(request):
    torneos = Torneo.objects.all()
    competencias = Competencia.objects.all()
    actividades = ActividadGeneral.objects.all()

    context = {
        "torneos": torneos,
        "competencias": competencias,
        "actividades": actividades,
    }
    return render(request, "persona/listado_eventos.html", context)

@login_required
def inscribirse_actividad_view(request):
    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)

    actividades_con_apto_vigente_ids = AptoGeneral.objects.filter(
        jugador=jugador,
        actividad__isnull=False
    ).exclude(estado="VENCIDO").values_list("actividad_id", flat=True)

    actividades_disponibles = ActividadGeneral.objects.exclude(
        id__in=actividades_con_apto_vigente_ids
    )

    return render(request, "persona/inscribirse_actividad.html", {
        "actividades": actividades_disponibles,
    })



@login_required
def inscribirse_actividad(request, actividad_id):
    persona = get_persona_from_user(request.user)
    jugador = get_object_or_404(Jugador, persona=persona)
    actividad = get_object_or_404(ActividadGeneral, id=actividad_id)

    ya_vigente = AptoGeneral.objects.filter(
        jugador=jugador, actividad=actividad
    ).exclude(estado="VENCIDO").exists()

    if ya_vigente:
        messages.info(request, "Ya estás inscripto en esta actividad.")
        return redirect("menu_paciente")

    registro_vencido = AptoGeneral.objects.filter(
        jugador=jugador, actividad=actividad, estado="VENCIDO"
    ).first()

    apto = AptoGeneral.objects.create(
        jugador=jugador,
        actividad=actividad,
        estado="PROCESO",
        consentimiento_persona=True,
        observacion="Inscripción a actividad"
        + (" (reinscripción por vencimiento)" if registro_vencido else " nueva")
    )

    AntecedenteAptoGeneral.objects.get_or_create(
        apto=apto,
        jugador=jugador
    )

    messages.success(
        request,
        f"Te inscribiste en {actividad.nombre}. Completá los antecedentes médicos."
    )

    # 🔥 REDIRECCIÓN CORRECTA
    return redirect(
        "aptos_generales:antecedentes_update",
        apto_id=apto.id
    )



