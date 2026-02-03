from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from estudiante.models import Tutor
from .forms import LoginForm, UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.contrib.auth import logout
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.contrib import messages
from django import forms
from Medico.models import Medico,Documentos
from persona.models import Persona,Jugador
from django.contrib.auth.models import User
from .models import Profile
import requests
from persona.utils import get_persona_from_user
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings


# Vista personalizada para recuperar contraseña
def enviar_recuperacion_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No hay una cuenta con ese correo.')
            return redirect('enviar_recuperacion')

        # Generar uid, token y URL segura
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        reset_url = request.build_absolute_uri(reset_path)

        # Texto del email
        subject = "Recuperación de contraseña - Checkeate"
        message = f"""
Hola {user.first_name},

Recibimos una solicitud para restablecer tu contraseña.

Hacé clic en el siguiente enlace para continuar:

{reset_url}

Si no solicitaste este cambio, podés ignorar este mensaje.

Gracias,
El equipo de Checkeate
"""

        # Envío con cuenta soporte
        soporte_user = settings.EMAIL_ACCOUNTS['soporte']['EMAIL_HOST_USER']
        soporte_pass = settings.EMAIL_ACCOUNTS['soporte']['EMAIL_HOST_PASSWORD']

        send_mail(
            subject,
            message,
            soporte_user,
            [email],
            fail_silently=False,
            auth_user=soporte_user,
            auth_password=soporte_pass
        )

        messages.success(request, 'Te enviamos un correo para restablecer tu contraseña.')
        return redirect('password_reset_done')  # ✅ redirige a página de confirmación

    return render(request, 'registration/enviar_recuperacion.html')




@login_required
def dashboard(request):
    return redirect('persona/registrar')

@never_cache
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'Usuario o contraseña incorrectos.')
                return redirect('login')

            user = authenticate(request, username=user.username, password=password)

            if user:
                return login_user_and_redirect(request, user)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
                return redirect('login')
    else:
        form = LoginForm()

    return render(request, 'account/login.html', {'form': form})


@login_required
def check_session(request):
    session_key = request.session.session_key

    if not session_key:
        return JsonResponse({'session_expired': True})

    try:
        session = Session.objects.get(session_key=session_key)

        if session.expire_date < now():
            return JsonResponse({'session_expired': True})

        return JsonResponse({'session_expired': False})

    except Session.DoesNotExist:
        return JsonResponse({'session_expired': True})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('login')

def terminos_condiciones(request):
    return render(request, 'account/terminos_condiciones.html')


def recover_Password(request):
    return render(request, 'account/password_change_form.html')



# Función para generar usernames únicos combinando email y rol
def generate_unique_username(email, role):
    return f"{email}_{role}"




def login_user_and_redirect(request, user):
    login(request, user)

    profiles = Profile.objects.filter(user=user)
    if not profiles.exists():
        print("❌ No se encontró un perfil para este usuario.")
        return redirect('login')

    if profiles.count() > 1:
        return redirect('select_role')

    profile = profiles.first()
    print("Usuario autenticado con rol:", profile.rol)

    request.session['user_profile_id'] = profile.id

    if profile.rol == 'estudiante':
        tutor_asociado = Tutor.objects.filter(profile=profile).exists()
        if not tutor_asociado:
            return redirect('cargar_tutor')
        return redirect('menu_estudiante')

    # 🔍 Verificación especial para médicos
    if profile.rol == 'medico':
        try:
            medico = Medico.objects.get(profile=profile)
        except Medico.DoesNotExist:
            print("❌ No se encontró el perfil médico.")
            return redirect('login')

        try:
            doc = medico.documentacion
            if not (doc.certificado_matricula and doc.certificado_firma_electronica and doc.contrato_aceptado):
                print("⚠️ Faltan documentos obligatorios del médico.")
                return redirect('cargar_documentacion')
        except Documentos.DoesNotExist:
            print("⚠️ El médico no tiene documentación cargada.")
            return redirect('cargar_documentacion')

        return redirect('seleccionar_apto')

    # 🔍 Nuevo: flujo para pacientes
    if profile.rol == 'paciente':
        from persona.models import Persona  # asegurate de importar arriba si lo usás mucho
        persona_asociada = Persona.objects.filter(profile=profile).exists()
        if not persona_asociada:
            return redirect('registrar_persona')
        return redirect('menu_paciente')

    # Otros roles
    if profile.rol == 'general':
        return redirect('menu_jugador')
    elif profile.rol == 'representante':
        return redirect('representante_home')
    elif profile.rol == 'colegio':
        return redirect('colegio_home')
    elif profile.rol == 'jugador':
        return redirect('menu_jugador')
    elif profile.rol == 'estudiante':
        return redirect('menu_estudiante')
    elif profile.rol == 'actividad':
        return redirect ('representante_actividad_general_home')
    else:
        return redirect('home')



@login_required
def select_role(request):
    user = request.user
    profiles = Profile.objects.filter(user=user)
    print(f"👤 Usuario logueado: {user} (ID: {user.id})")
    print(f"📑 Roles encontrados: {[p.rol for p in profiles]}")

    if not profiles.exists():
        print("❌ No hay perfiles asociados al usuario.")
        return redirect('login')

    if request.method == "POST":
        selected_role = request.POST.get("role")
        print(f"➡️ Rol seleccionado: {selected_role}")

        try:
            profile = profiles.get(rol=selected_role)
            print(f"✅ Profile encontrado: {profile} (rol={profile.rol}, id={profile.id})")

            request.session["user_profile_id"] = profile.id
            request.session["user_profile_rol"] = profile.rol

            # 🔄 Redirección según el rol seleccionado
            if profile.rol == "jugador":
                persona, _ = Persona.objects.get_or_create(user=request.user)
                jugador = Jugador.objects.filter(persona=persona).first()
                print(f"🎯 Jugador -> persona={persona}, jugador={jugador}")

                if jugador:
                    print("✅ Jugador encontrado → redirigiendo a menu_jugador")
                    return redirect("menu_jugador")
                else:
                    print("⚠️ No hay jugador asociado → redirigiendo a registrar_persona")
                    return redirect("registrar_persona")

            elif profile.rol == "estudiante":
                print("🎯 Rol estudiante → redirigiendo a menu_estudiante")
                return redirect("menu_estudiante")

            elif profile.rol == "medico":
                print("🎯 Rol médico → validando documentación")

                try:
                    medico = Medico.objects.get(profile=profile)
                except Medico.DoesNotExist:
                    print("❌ No se encontró Medico asociado al profile")
                    return redirect("cargar_documentacion")

                # Si no hay documentos asociados, obligar a cargarlos
                if not hasattr(medico, "documentacion"):
                    print("⚠️ Médico sin documentos → redirigiendo a cargar_documentacion")
                    return redirect("cargar_documentacion")

                doc = medico.documentacion

                if not (doc.certificado_matricula and doc.qr_valido and
                        doc.certificado_firma_electronica and doc.contrato_aceptado):
                    print("⚠️ Documentación incompleta o inválida → redirigiendo a cargar_documentacion")
                    return redirect("cargar_documentacion")

                print("✅ Documentación validada → redirigiendo a seleccionar_apto")
                return redirect("seleccionar_apto")


            elif profile.rol == "representante":
                print("🎯 Rol representante → redirigiendo a representante_home")
                return redirect("representante_home")

            elif profile.rol == "paciente":
                persona, _ = Persona.objects.get_or_create(user=request.user)

                print(f"🎯 Paciente -> persona={persona}")
                if persona and persona.direccion and persona.telefono:
                    print("✅ Persona completa → redirigiendo a menu_paciente")
                    return redirect("menu_paciente")
                else:
                    print("⚠️ Persona incompleta → redirigiendo a registrar_persona")
                    return redirect("registrar_persona")

            else:
                print("⚠️ Rol no reconocido → redirigiendo a home")
                return redirect("home")

        except Profile.DoesNotExist:
            print("❌ Profile no encontrado para el rol seleccionado")
            return redirect("select_role")

    print("📌 GET inicial → mostrando template select_role")
    return render(request, "account/select_role.html", {"profiles": profiles})



def preparar_formulario_existente(email, rol):
    form = UserRegistrationForm(initial={'email': email}, rol=rol)
    campos_ocultos = ['nombre', 'apellido', 'dni', 'fecha_nacimiento', 'password2']
    for campo in campos_ocultos:
        form.fields[campo].widget = forms.HiddenInput()
        form.fields[campo].required = False
        form.fields[campo].widget.attrs['readonly'] = True
    return form

def register(request):
    print(f"📥 Request recibido: {request.method} en {request.path}")

    # 🔎 Detectamos rol en base al path
    user_role = "jugador"
    if request.path == "/account/register_alumnos/":
        user_role = "estudiante"
    elif request.path == "/account/register_paciente/":
        user_role = "paciente"

    # ✅ VALIDACIÓN ANTES DE MOSTRAR EL FORMULARIO COMPLETO
    if request.method == 'GET' and 'email' in request.GET:
        email = request.GET.get('email')
        user = User.objects.filter(email=email).first()

        print(f"🔎 Usuario encontrado para {email}: {user}")

        if user:
            if Profile.objects.filter(user=user, rol=user_role).exists():
                messages.error(request, f"Ya estás registrado como {user_role}. Iniciá sesión para continuar.")
                return redirect('login')

            # Si el usuario existe pero no con este rol → mostrar form reducido (solo contraseña)
            form = preparar_formulario_existente(email, user_role)

            if user_role == "jugador":
                template = "account/register.html"
            elif user_role == "estudiante":
                template = "account/estudiante/register.html"
            elif user_role == "paciente":
                template = "account/paciente/register.html"

            return render(request, template, {
                'verificar_password': True,
                'email': email,
                'user_form': form
            })

    # 🧾 REGISTRO POST
    if request.method == 'POST':
        print("📨 Se recibió POST")
        print("📥 POST DATA:", request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password1')

        try:
            # Usuario ya existe
            user_existente = User.objects.get(email=email)
            print("⚠️ Ya existe un usuario con ese email")

            user_auth = authenticate(request, username=user_existente.username, password=password)

            if user_auth is None:
                messages.error(request, "Contraseña incorrecta para el email proporcionado.")
                form = preparar_formulario_existente(email, user_role)
                form.fields['email'].initial = ''

                if user_role == "jugador":
                    template = "account/register.html"
                elif user_role == "estudiante":
                    template = "account/estudiante/register.html"
                elif user_role == "paciente":
                    template = "account/paciente/register.html"

                return render(request, template, {'user_form': form})

            if Profile.objects.filter(user=user_existente, rol=user_role).exists():
                messages.error(request, f"Ya estás registrado en esta sección como {user_role}. Por favor, iniciá sesión.")
                return redirect('login')

            # 🔄 Heredar datos de otro perfil si existe
            otro_perfil = Profile.objects.filter(user=user_existente).first()

            nombre = request.POST.get('nombre') or (otro_perfil.nombre if otro_perfil else '')
            apellido = request.POST.get('apellido') or (otro_perfil.apellido if otro_perfil else '')
            dni = request.POST.get('dni') or (otro_perfil.dni if otro_perfil else '')
            fecha_nacimiento = request.POST.get('fecha_nacimiento') or (otro_perfil.fecha_nacimiento if otro_perfil else None)

            # 🔎 Buscar persona ya asociada a este usuario
            persona_existente = Persona.objects.filter(profile__user=user_existente).first()

            profile = Profile.objects.create(
                user=user_existente,
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                fecha_nacimiento=fecha_nacimiento,
                email=email,
                rol=user_role
            )
            request.session['user_profile_id'] = profile.id

            # 👉 Vincular persona existente al nuevo profile
            if persona_existente:
                persona_existente.profile = profile
                persona_existente.save()
                print(f"♻️ Persona {persona_existente} vinculada al nuevo profile {profile.rol}")

            # 👉 Redirigir según roles
            roles_totales = Profile.objects.filter(user=user_existente).count()
            if roles_totales > 1:
                return redirect("select_role")

            if user_role == "paciente":
                if not persona_existente:
                    return redirect("registrar_persona")
                return redirect("menu_paciente")

            return redirect("select_role")

        except User.DoesNotExist:
            # Usuario nuevo
            form = UserRegistrationForm(request.POST, rol=user_role)
            if form.is_valid():
                user, profile = form.save()
                request.session['user_profile_id'] = profile.id

                if Profile.objects.filter(user=user).count() > 1:
                    return redirect("select_role")

                if user_role == "paciente":
                    return redirect("registrar_persona")
                else:
                    return redirect('select_role')
            else:
                print("❌ Errores del formulario:", form.errors)
                messages.error(request, "Error en el registro. Verifica los datos.")
    else:
        form = UserRegistrationForm(rol=user_role)
        form.fields['email'].initial = ''

    # Selección del template según rol
    if user_role == "jugador":
        template = "account/register.html"
    elif user_role == "estudiante":
        template = "account/estudiante/register.html"
    elif user_role == "paciente":
        template = "account/paciente/register.html"

    return render(request, template, {'user_form': form})





def verificar_email(request):
    email = request.GET.get('email')
    rol_deseado = request.GET.get('rol')  # opcional, 'jugador', 'estudiante', etc.
    data = {'existe': False, 'tiene_rol': False}

    if email:
        try:
            user = User.objects.get(email=email)
            data['existe'] = True
            print(f"Usuario encontrado: {user.email}")

            perfiles = Profile.objects.filter(user=user)
            if perfiles.exists():
                if rol_deseado:
                    perfil_rol = perfiles.filter(rol=rol_deseado).first()
                    if perfil_rol:
                        data['tiene_rol'] = True
                        data['rol'] = perfil_rol.rol
                        print(f"Ya tiene rol {rol_deseado}")
                    else:
                        print(f"El usuario no tiene el rol {rol_deseado}")
                else:
                    primer_perfil = perfiles.first()
                    data['rol'] = primer_perfil.rol
                    print(f"Rol del primer perfil encontrado: {primer_perfil.rol}")
            else:
                print("El usuario no tiene perfiles asociados.")

        except User.DoesNotExist:
            print("No se encontró el usuario con ese email.")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")

    return JsonResponse(data)


def notificar_whatsapp_medico(medico):
    telefono = "5493516807765"  # tu número en formato internacional (ej: 54911...)
    api_key = "3417172"     # la API key que te dio CallMeBot

    mensaje = (
        f"📢 Nuevo Médico Registrado en Checkeate\n"
        f"👨‍⚕️ Nombre: {medico.profile.nombre} {medico.profile.apellido}\n"
        f"📧 Email: {medico.profile.email}\n"
        f"🏥 Especialidad: {medico.especialidad or 'No cargada'}"
    )

    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={telefono}&text={mensaje}&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ WhatsApp enviado correctamente")
        else:
            print(f"⚠️ Error al enviar WhatsApp: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al enviar WhatsApp: {e}")


def register_medico(request):
    rol = "medico"

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password1')

        try:
            # Caso: el usuario ya existe
            user_existente = User.objects.get(email=email)
            print(f"⚠️ Usuario ya existente: {user_existente}")

            # Verificar contraseña
            user_auth = authenticate(request, username=user_existente.username, password=password)
            if user_auth is None:
                messages.error(request, "Contraseña incorrecta para este email.")
                return render(request, 'account/register_medico.html', {
                    'user_form': UserRegistrationForm(rol=rol)
                })

            # Verificar si ya tiene rol médico
            if Profile.objects.filter(user=user_existente, rol=rol).exists():
                messages.error(request, "Ya estás registrado como médico. Iniciá sesión.")
                return redirect('login')

            # Heredar datos de otro perfil si existe
            otro_perfil = Profile.objects.filter(user=user_existente).first()

            profile = Profile.objects.create(
                user=user_existente,
                nombre=otro_perfil.nombre if otro_perfil else '',
                apellido=otro_perfil.apellido if otro_perfil else '',
                dni=otro_perfil.dni if otro_perfil else '',
                fecha_nacimiento=otro_perfil.fecha_nacimiento if otro_perfil else None,
                email=email,
                rol=rol
            )

            # Crear objeto Medico vinculado
            medico, _ = Medico.objects.get_or_create(profile=profile)

            # 📲 Notificar por WhatsApp
            notificar_whatsapp_medico(medico)

            messages.success(request, "Se agregó el rol médico a tu cuenta. Ahora podés iniciar sesión.")
            return redirect('login')

        except User.DoesNotExist:
            # Caso: usuario nuevo → form completo
            form = UserRegistrationForm(request.POST, rol=rol)
            if form.is_valid():
                user, profile = form.save()
                medico, _ = Medico.objects.get_or_create(profile=profile)

                # 📲 Notificar también en este caso
                notificar_whatsapp_medico(medico)

                messages.success(request, "Registro exitoso. Ahora podés iniciar sesión.")
                return redirect('login')
            else:
                print("❌ Errores del formulario médico:", form.errors)
                messages.error(request, "Error en el registro. Verificá los datos.")
                return render(request, 'account/register_medico.html', {'user_form': form})

    else:
        form = UserRegistrationForm(rol=rol)

    return render(request, 'account/register_medico.html', {'user_form': form})



def verificar_dni(request):
    dni = request.GET.get('dni', None)
    data = {
        'existe': False
    }
    if dni and Profile.objects.filter(dni=dni).exists():
        data['existe'] = True
    return JsonResponse(data)
