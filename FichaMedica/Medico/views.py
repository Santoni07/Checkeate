from django.contrib import messages
from django.http import HttpResponse
import requests
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode
from weasyprint import HTML
from django.utils.html import format_html
from django.http import HttpResponse
from django.views.generic import ListView
from django.db.models import Q
from django.db import transaction
from weasyprint import HTML
from account.models import Profile
from persona.models import Jugador,JugadorCategoriaEquipo
from RegistroMedico.models import RegistroMedico, AntecedenteEnfermedades as AntecedentesModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from Cus.models import Cus
from django.views import View
from RegistroMedico.forms import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse
from estudiante.models import Estudiante, AntecedentesCUS
from account.models import Profile
from Medico.models import Documentos, Medico
from Medico.forms import DocumentosForm,MedicoDatosComplementariosForm
from Cus.models import *
from Cus.form import *
from core.utils.email_utils import enviar_correo
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from aptos_generales.models import *
from aptos_generales.forms import *
from weasyprint import HTML, CSS
from django.conf import settings
import os
from django.contrib.staticfiles import finders
import qrcode
import base64
from io import BytesIO
from django.urls import reverse
from persona.models import Persona
import io


@login_required
def seleccionar_apto(request):
    profile_id = request.session.get("user_profile_id")
    print(f"🔍 Profile ID: {profile_id}")
    profile = Profile.objects.filter(id=profile_id).first()

    medico = Medico.objects.filter(profile=profile).first() if profile else None
    print(f"🔍 Medico asociado al perfil: {medico}")

    context = {
        'search_dni': request.GET.get('search_dni', ''),
        'search_name': request.GET.get('search_name', ''),
        'profile': profile,
        'medico': medico,
    }

    return render(request, 'medico/seleccionar_apto.html', context)

#################### VISTAS PARA LOS APTOS FISICOS DEPORTIVOS  ####################



class MedicoHomeView(ListView):
    model = Jugador
    template_name = 'medico/medico_home.html'
    context_object_name = 'jugadores'

    # ---------------------------
    # Búsqueda
    # ---------------------------
    def get_queryset(self):
        queryset = Jugador.objects.all()
        search_dni = self.request.GET.get('search_dni', '').strip()
        search_name = self.request.GET.get('search_name', '').strip()

        # sin filtros => no muestres nada
        if not search_dni and not search_name:
            return Jugador.objects.none()

        if search_dni:
            if search_dni.isdigit() and len(search_dni) == 8:
                queryset = queryset.filter(persona__profile__dni__icontains=search_dni)
            else:
                messages.error(self.request, "El DNI ingresado debe contener exactamente 8 números.")
                return Jugador.objects.none()

        if search_name:
            palabras = search_name.split()
            consulta = Q()
            if len(palabras) == 1:
                consulta = (
                    Q(persona__profile__nombre__icontains=palabras[0]) |
                    Q(persona__profile__apellido__icontains=palabras[0])
                )
            elif len(palabras) >= 2:
                p1, p2 = palabras[0], palabras[1]
                consulta = (
                    Q(persona__profile__nombre__icontains=p1, persona__profile__apellido__icontains=p2) |
                    Q(persona__profile__apellido__icontains=p1, persona__profile__nombre__icontains=p2)
                )
            queryset = queryset.filter(consulta)

        return queryset

    # ---------------------------
    # Contexto
    # ---------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # valores de búsqueda para mantener inputs
        context['search_dni'] = self.request.GET.get('search_dni', '')
        context['search_name'] = self.request.GET.get('search_name', '')

        # perfil y médico
        profile_id = self.request.session.get("user_profile_id")
        profile = Profile.objects.filter(id=profile_id).first()
        context['profile'] = profile
        context['medico'] = Medico.objects.filter(profile=profile).first() if profile else None

        # ---------- RESUMEN (entre “Bienvenido” y el buscador) ----------
        hoy = timezone.localdate()
        filtros_medico = {}
        if context.get("medico"):
            filtros_medico["medico"] = context["medico"]

        qs = RegistroMedico.objects.filter(**filtros_medico)
        context["hoy"] = hoy
        context["pendientes_count"]     = qs.filter(estado="PROCESO").count()
        context["aprobadas_hoy_count"]  = qs.filter(estado="APROBADA").count()
        context["rechazadas_hoy_count"] = qs.filter(estado="RECHAZADA").count()
        # ----------------------------------------------------------------

        # Armar tabla de jugadores/regs (ahora maneja torneos y competencias)
        jugadores_info = []
        if 'jugadores' in context and context['jugadores'].exists():
            for jugador in context['jugadores']:
                registros_medicos = (
                    RegistroMedico.objects
                    .filter(jugador=jugador)
                    .select_related('torneo', 'competencia', 'jugador__persona__profile')
                )

                for registro in registros_medicos:
                    # Si es un registro por TORNEO
                    if registro.torneo_id:
                        jce = (
                            JugadorCategoriaEquipo.objects
                            .filter(
                                jugador=jugador,
                                categoria_equipo__categoria__torneo=registro.torneo
                            )
                            .select_related('categoria_equipo__categoria', 'categoria_equipo__equipo')
                            .first()
                        )
                        categoria = jce.categoria_equipo.categoria.nombre if jce else "Sin categoría"
                        equipo    = jce.categoria_equipo.equipo.nombre    if jce else "Sin equipo"
                        evento_tipo   = "TORNEO"
                        evento_nombre = registro.torneo.nombre

                    # Si es un registro por COMPETENCIA
                    else:
                        categoria = "—"
                        equipo    = "—"
                        evento_tipo   = "COMPETENCIA"
                        evento_nombre = registro.competencia.nombre if registro.competencia else "Sin competencia"

                    jugadores_info.append({
                        'id': jugador.id,
                        'dni': jugador.persona.profile.dni,
                        'nombre': jugador.persona.profile.nombre,
                        'apellido': jugador.persona.profile.apellido,
                        'categoria': categoria,
                        'equipo': equipo,
                        # mantenemos la key 'torneo' para no tocar tu template:
                        'torneo': evento_nombre,      # si es competencia, va el nombre de la competencia
                        'evento_tipo': evento_tipo,   # por si querés mostrar un badge en el template
                        'estado': registro.estado,
                        'registro_id': registro.id,
                    })
        has_torneos = any(j.get('evento_tipo') == 'TORNEO' for j in jugadores_info)
        has_competencias = any(j.get('evento_tipo') == 'COMPETENCIA' for j in jugadores_info)
        context['jugadores_info'] = jugadores_info
        context['has_torneos'] = has_torneos
        context['has_competencias'] = has_competencias
        return context

    # ---------------------------
    # Carga de estudio (POST)
    # ---------------------------
    def post(self, request, *args, **kwargs):
        form_saved = False
        jugador_id = request.POST.get('jugador_id')
        registro_id = request.POST.get('registro_id')

        form = EstudioMedicoForm(request.POST, request.FILES)
        if form.is_valid():
            jugador = get_object_or_404(Jugador, id=jugador_id)
            registro_medico = get_object_or_404(RegistroMedico, id=registro_id, jugador=jugador)

            estudio = form.save(commit=False)
            estudio.ficha_medica = registro_medico
            estudio.save()

            messages.success(request, "✅ Estudio médico cargado exitosamente.")
            form_saved = True
        else:
            messages.error(request, "❌ Hubo un error al cargar el estudio médico.")

        # recargar queryset y contexto
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['form_saved'] = form_saved
        context['jugador_id'] = jugador_id
        context['registro_id'] = registro_id

        return render(request, 'medico/medico_home.html', context)


#Manejo de los formularios
def manejar_formulario_medico(request, jugador_id, registro_id, modelo, formulario_clase, template_name='medico/medico_home.html'):

    print(f"🛠 Debug - jugador_id: {jugador_id}, registro_id: {registro_id} (Tipo: {type(registro_id)})")

    # Validar que registro_id sea un número entero
    try:
        registro_id = int(registro_id)
    except ValueError:
        return HttpResponse("Error: registro_id debe ser un número entero.", status=400)

    # Obtener jugador y registro médico
    jugador = get_object_or_404(Jugador, id=jugador_id)
    registro_medico = get_object_or_404(RegistroMedico, id=registro_id, jugador=jugador)

    print(f"✅ Registro Médico encontrado: {registro_medico}")

    # Buscar la instancia del modelo relacionado con la ficha médica
    instancia = modelo.objects.filter(ficha_medica=registro_medico).first()

    if request.method == 'POST':
        formulario = formulario_clase(request.POST, instance=instancia)
        if formulario.is_valid():
            with transaction.atomic():
                instancia = formulario.save(commit=False)
                instancia.ficha_medica = registro_medico
                instancia.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Formulario guardado exitosamente."})
    else:
        formulario = formulario_clase(instance=instancia)

    return render(request, template_name, {
        'jugador': jugador,
        f'{modelo.__name__.lower()}_form': formulario,
    })


# Vistas utilizando la función genérica
def electro_basal_view(request, jugador_id, registro_id):
   return manejar_formulario_medico(request, jugador_id, registro_id, ElectroBasal, ElectroBasalForm)

def electro_esfuerzo_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, ElectroEsfuerzo, ElectroEsfuerzoForm)

def otros_examenes_clinicos_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, OtrosExamenesClinicos, OtrosExamenesClinicosForm)

def cardiovascular_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, Cardiovascular, CardiovascularForm)

def laboratorio_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, Laboratorio, LaboratorioForm)

def torax_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, Torax, ToraxForm)

def oftalmologico_view(request, jugador_id, registro_id):
    return manejar_formulario_medico(request, jugador_id, registro_id, Oftalmologico, OftalmologicoForm)



# Registro_medico_cargar
@login_required
def registro_medico_update_view(request, registro_id):
    registro_medico = get_object_or_404(RegistroMedico, id=registro_id)
    jugador = registro_medico.jugador

    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()

    # ---- flags de tipo de evento ----
    es_torneo = bool(registro_medico.torneo_id)
    es_competencia = bool(registro_medico.competencia_id)
    requiere_estudios = es_torneo  # competencias NO requieren estudios

    estado_anterior = registro_medico.estado

    if request.method == 'POST':
        registro_medico_form = RegistroMedicoUpdateForm(request.POST, instance=registro_medico)
        estudio_medico_form = EstudioMedicoForm(request.POST, request.FILES)

        # ✅ Cargar Estudio Médico (opcional también para competencias)
        if 'cargar_estudio' in request.POST:
            if estudio_medico_form.is_valid():
                estudio = estudio_medico_form.save(commit=False)
                # Tus estudios están asociados al jugador (según tu implementación actual)
                estudio.jugador = jugador
                estudio.save()
                messages.success(request, "✅ Estudio médico cargado exitosamente.")
            else:
                messages.error(request, "❌ Error al cargar el estudio médico.")
                return redirect(f"{reverse('registro_medico_update_view', kwargs={'registro_id': registro_medico.id})}?abrir=estudios")

        # ✅ Guardar Registro Médico sin aprobar
        elif 'guardar_registro' in request.POST:
            if registro_medico_form.is_valid():
                with transaction.atomic():
                    registro = registro_medico_form.save(commit=False)
                    registro.estado = registro.estado or estado_anterior
                    registro.medico = Medico.objects.filter(profile=profile).first()
                    registro.save()
                    messages.success(request, "✅ Ficha médica actualizada.")
                    return redirect('medico_home')
            else:
                messages.error(request, "❌ Error al actualizar la ficha médica.")

        # ✅ Guardar Ficha Completa y Aprobar
        elif 'guardar_ficha_completa' in request.POST:
            with transaction.atomic():
                if registro_medico_form.is_valid():
                    registro = registro_medico_form.save(commit=False)
                    registro.estado = "APROBADA"
                    registro.medico = Medico.objects.filter(profile=profile).first()
                    registro.save()

                    # 🔔 Enviar correo una sola vez
                    try:
                        destinatario = (registro.jugador.persona.profile.user.email or "").strip()
                        fecha_venc = registro.fecha_caducidad.strftime("%d/%m/%Y") if registro.fecha_caducidad else "sin definir"
                        asunto = "✅ Registro médico aprobado"
                        cuerpo = f"""
                        Hola {registro.jugador.persona.profile.nombre},

                        Tu registro médico para el evento fue aprobado.
                        Fecha de vencimiento: {fecha_venc}.

                        Consultá tu ficha en:
                        https://www.checkeate.com.ar

                        ¡Éxitos!
                        """
                        enviar_correo(asunto, cuerpo, [destinatario], "notificaciones", tipo="registro")
                    except Exception as e:
                        print(f"❌ Error al enviar correo: {e}")

                    messages.success(request, "✅ Ficha médica completada y aprobada.")
                else:
                    messages.error(request, "❌ Error en ficha médica.")

            return redirect('medico_home')
    else:
        registro_medico_form = RegistroMedicoUpdateForm(instance=registro_medico)
        estudio_medico_form = EstudioMedicoForm()

    # ---- Datos del torneo/categoría/equipo (solo si es torneo) ----
    jugador_categoria_equipo = None
    if es_torneo:
        jugador_categoria_equipo = (
            JugadorCategoriaEquipo.objects
            .filter(jugador=jugador, categoria_equipo__categoria__torneo=registro_medico.torneo)
            .select_related('categoria_equipo__categoria', 'categoria_equipo__equipo')
            .first()
        )

    # ---- Estudios existentes (asociados al jugador) ----
    estudios_qs = EstudiosMedico.objects.filter(jugador=jugador)

    # ---- Requisitos (para el gating en template) ----
    electrocardiograma_cargado = EstudiosMedico.objects.filter(jugador=jugador, tipo_estudio='ELECTRO').exists()
    ergonometria_cargado = EstudiosMedico.objects.filter(jugador=jugador, tipo_estudio='ERGOMETRIA').exists()

    # Para competencias no se requieren: podés dejarlos como están y usar 'requiere_estudios' en el template,
    # o marcarlos True para no bloquear. Dejamos el flag para decidir en la vista:
    if es_competencia:
        electrocardiograma_cargado = True
        ergonometria_cargado = True

    # ---- Info de evento para mostrar en pantalla ----
    evento_nombre = (
        registro_medico.torneo.nombre if es_torneo
        else (registro_medico.competencia.nombre if es_competencia else "—")
    )

    context = {
        'jugador': jugador,
        'profile': profile,

        'registro_medico': registro_medico,
        'registro_medico_form': registro_medico_form,
        'estudio_medico_form': estudio_medico_form,

        # datos del jugador
        'nombre': jugador.persona.profile.nombre,
        'apellido': jugador.persona.profile.apellido,
        'edad': jugador.persona.profile.edad,
        'dni': jugador.persona.profile.dni,
        'direccion': jugador.persona.direccion,
        'telefono': jugador.persona.telefono,
        'grupo_sanguineo': jugador.grupo_sanguineo,
        'cobertura_medica': jugador.cobertura_medica,
        'numero_afiliado': jugador.numero_afiliado,

        # torneo (si aplica) — mantenemos tus keys por compatibilidad
        'torneo_descripcion': registro_medico.torneo.descripcion if es_torneo else "",
        'torneo_direccion': registro_medico.torneo.direccion if es_torneo else "",
        'torneo_telefono': registro_medico.torneo.telefono if es_torneo else "",
        'imagen_torneo': registro_medico.torneo.imagen.url if es_torneo and registro_medico.torneo.imagen else None,
        'categoria': (jugador_categoria_equipo.categoria_equipo.categoria.nombre if jugador_categoria_equipo else "Sin categoría"),
        'equipo': (jugador_categoria_equipo.categoria_equipo.equipo.nombre if jugador_categoria_equipo else "Sin equipo"),

        # antecedentes y estudios
        'antecedentes': list(AntecedentesModel.objects.filter(jugador=jugador).values()),
        'estudios_medicos': estudios_qs,
        'electrocardiograma_cargado': electrocardiograma_cargado,
        'ergonometria_cargado': ergonometria_cargado,

        # forms de secciones
        'electro_basal_form': ElectroBasalForm(instance=ElectroBasal.objects.filter(ficha_medica=registro_medico).first() or ElectroBasal(ficha_medica=registro_medico)),
        'electro_esfuerzo_form': ElectroEsfuerzoForm(instance=ElectroEsfuerzo.objects.filter(ficha_medica=registro_medico).first() or ElectroEsfuerzo(ficha_medica=registro_medico)),
        'cardiovascular_form': CardiovascularForm(instance=Cardiovascular.objects.filter(ficha_medica=registro_medico).first() or Cardiovascular(ficha_medica=registro_medico)),
        'laboratorio_form': LaboratorioForm(instance=Laboratorio.objects.filter(ficha_medica=registro_medico).first() or Laboratorio(ficha_medica=registro_medico)),
        'oftalmologico_form': OftalmologicoForm(instance=Oftalmologico.objects.filter(ficha_medica=registro_medico).first() or Oftalmologico(ficha_medica=registro_medico)),
        'torax_form': ToraxForm(instance=Torax.objects.filter(ficha_medica=registro_medico).first() or Torax(ficha_medica=registro_medico)),
        'otros_examenes_form': OtrosExamenesClinicosForm(instance=OtrosExamenesClinicos.objects.filter(ficha_medica=registro_medico).first() or OtrosExamenesClinicos(ficha_medica=registro_medico)),

        # flags para el template
        'es_torneo': es_torneo,
        'es_competencia': es_competencia,
        'requiere_estudios': requiere_estudios,
        'evento_nombre': evento_nombre,  # usar en “Datos del torneo/competencia”
    }

    return render(request, 'medico/cargar_registro.html', context)

# medico_views(arma la ficha y la mustra, tambien descarga el pdf)
def ficha_medica_views(request, registro_id):
    registro_medico = get_object_or_404(RegistroMedico, id=registro_id)
    jugador = registro_medico.jugador

    # Flags de tipo de evento
    es_torneo = bool(registro_medico.torneo_id)
    es_competencia = bool(registro_medico.competencia_id)

    # Perfil / rol
    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()
    medico = Medico.objects.filter(profile=profile).first() if profile else None
    rol_usuario = profile.rol if profile else None


    # Buscar categoría/equipo solo si es torneo
    jugador_categoria_equipo = None
    if es_torneo:
        jugador_categoria_equipo = (
            JugadorCategoriaEquipo.objects
            .filter(
                jugador=jugador,
                categoria_equipo__categoria__torneo=registro_medico.torneo
            )
            .select_related('categoria_equipo__categoria', 'categoria_equipo__equipo')
            .first()
        )

    # Antecedentes (por jugador)
    antecedentes = AntecedentesModel.objects.filter(jugador=jugador)

    # Estudios del registro (si existen) – para competencias NO son obligatorios
    electro_basal     = ElectroBasal.objects.filter(ficha_medica=registro_medico).first()
    electro_esfuerzo  = ElectroEsfuerzo.objects.filter(ficha_medica=registro_medico).first()
    cardiovascular    = Cardiovascular.objects.filter(ficha_medica=registro_medico).first()
    laboratorio       = Laboratorio.objects.filter(ficha_medica=registro_medico).first()
    oftalmologico     = Oftalmologico.objects.filter(ficha_medica=registro_medico).first()
    torax             = Torax.objects.filter(ficha_medica=registro_medico).first()
    otros_examenes    = OtrosExamenesClinicos.objects.filter(ficha_medica=registro_medico).first()

    # URLs absolutas para imágenes (útil para PDF)
    imagen_torneo_abs = None
    if (
        es_torneo and jugador_categoria_equipo and
        getattr(jugador_categoria_equipo.categoria_equipo.categoria.torneo, "imagen", None)
    ):
        imagen_torneo_abs = request.build_absolute_uri(
            jugador_categoria_equipo.categoria_equipo.categoria.torneo.imagen.url
        )

    imagen_competencia_abs = None
    if es_competencia and getattr(registro_medico.competencia, "imagen", None):
        imagen_competencia_abs = request.build_absolute_uri(
            registro_medico.competencia.imagen.url
        )

    # Firma del médico absoluta (si existe)
    if registro_medico.medico and getattr(registro_medico.medico, "firma", None):
        registro_medico.medico.firma = request.build_absolute_uri(registro_medico.medico.firma.url)

        # Generar URL de validación del certificado (por ejemplo: https://checkeate.com.ar/validar-certificado/123/)

    qr_code= generar_qr_certificado(request, "registro", registro_medico.id)
    # Armar info para el template
    jugador_info = {
        'id': jugador.id,
        'edad': jugador.persona.profile.edad,
        'dni': jugador.persona.profile.dni,
        'nombre': jugador.persona.profile.nombre,
        'apellido': jugador.persona.profile.apellido,
        'direccion': jugador.persona.direccion,
        'telefono': jugador.persona.telefono,
        'grupo_sanguineo': jugador.grupo_sanguineo,
        'cobertura_medica': jugador.cobertura_medica,
        'numero_afiliado': jugador.numero_afiliado,

        # --- TORNEO ---
        'es_torneo': es_torneo,
        'torneo': (
            jugador_categoria_equipo.categoria_equipo.categoria.torneo.nombre
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.categoria)
            else "Sin torneo"
        ),
        'categoria': (
            jugador_categoria_equipo.categoria_equipo.categoria.nombre
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.categoria)
            else "Sin categoría"
        ),
        'equipo': (
            jugador_categoria_equipo.categoria_equipo.equipo.nombre
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.equipo)
            else "Sin equipo"
        ),
        'imagen_torneo': imagen_torneo_abs,
        'torneo_descripcion': (
            jugador_categoria_equipo.categoria_equipo.categoria.torneo.descripcion
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.categoria)
            else ""
        ),
        'torneo_direccion': (
            jugador_categoria_equipo.categoria_equipo.categoria.torneo.direccion
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.categoria)
            else ""
        ),
        'torneo_telefono': (
            jugador_categoria_equipo.categoria_equipo.categoria.torneo.telefono
            if (jugador_categoria_equipo and jugador_categoria_equipo.categoria_equipo and jugador_categoria_equipo.categoria_equipo.categoria)
            else ""
        ),

        # --- COMPETENCIA ---
        'es_competencia': es_competencia,
        'competencia_nombre': registro_medico.competencia.nombre if es_competencia else "",
        'competencia_descripcion': getattr(registro_medico.competencia, "descripcion", "") if es_competencia else "",
        'competencia_direccion': getattr(registro_medico.competencia, "direccion", "") if es_competencia else "",
        'competencia_telefono': getattr(registro_medico.competencia, "telefono", "") if es_competencia else "",
        'imagen_competencia': imagen_competencia_abs,

        # Antecedentes (por jugador)
        'antecedentes': [
            {
                'fue_operado': ant.fue_operado,
                'toma_medicacion': ant.toma_medicacion,
                'estuvo_internado': ant.estuvo_internado,
                'sufre_hormigueos': ant.sufre_hormigueos,
                'es_diabetico': ant.es_diabetico,
                'es_asmatico': ant.es_asmatico,
                'es_alergico': ant.es_alergico,
                'alerg_observ': ant.alerg_observ,
                'antecedente_epilepsia': ant.antecedente_epilepsia,
                'desviacion_columna': ant.desviacion_columna,
                'dolor_cintura': ant.dolor_cintura,
                'fracturas': ant.fracturas,
                'dolores_articulares': ant.dolores_articulares,
                'falta_aire': ant.falta_aire,
                'traumatismos_craneo': ant.traumatismos_craneo,
                'dolor_pecho': ant.dolor_pecho,
                'perdida_conocimiento': ant.perdida_conocimiento,
                'presion_arterial': ant.presion_arterial,
                'muerte_subita_familiar': ant.muerte_subita_familiar,
                'enfermedad_cardiaca_familiar': ant.enfermedad_cardiaca_familiar,
                'soplo_cardiaco': ant.soplo_cardiaco,
                'abstenerce_competencia': ant.abstenerse_competencia,
                'antecedentes_coronarios_familiares': ant.antecedentes_coronarios_familiares,
                'fumar_hipertension_diabetes': ant.fumar_hipertension_diabetes,
                'consumo_cocaina_anabolicos': ant.consumo_cocaina_anabolicos,
                'cca_observaciones': ant.cca_observaciones,
            }
            for ant in antecedentes
        ],

        # Formularios (solo si hay instancia)
        'electro_basal_form': ElectroBasalForm(instance=electro_basal) if electro_basal else None,
        'electro_esfuerzo_form': ElectroEsfuerzoForm(instance=electro_esfuerzo) if electro_esfuerzo else None,
        'cardiovascular_form': CardiovascularForm(instance=cardiovascular) if cardiovascular else None,
        'laboratorio_form': LaboratorioForm(instance=laboratorio) if laboratorio else None,
        'oftalmologico_form': OftalmologicoForm(instance=oftalmologico) if oftalmologico else None,
        'torax_form': ToraxForm(instance=torax) if torax else None,
        'otros_examenes_form': OtrosExamenesClinicosForm(instance=otros_examenes) if otros_examenes else None,
    }

    # Descargar PDF si se solicita
    if request.GET.get('descargar_pdf') == 'true':
        html_content = render_to_string('medico/medico_views.html', {
            'jugador_info': jugador_info,
            'registro_medico': registro_medico,
            'rol_usuario': rol_usuario,
            'qr_code': qr_code,
        })
        # Extraer solo el bloque <section id="content">...</section>
        start_tag = '<section id="content">'
        end_tag = '</section>'
        content_start = html_content.find(start_tag)
        content_end = html_content.find(end_tag) + len(end_tag)
        content_to_pdf = html_content[content_start:content_end]

        html_string = f"""<!DOCTYPE html>
            <html lang="es">
            <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ficha Médica</title>
            <style>
              body {{ font-family: Arial, sans-serif; font-size: 8px; color:#333; margin:0; padding:0; }}
              h1,h2,h3,h4 {{ color:#0056b3; text-align:center; font-weight:bold; font-size:10px; margin:0; padding:0; }}
              p {{ margin:0; line-height:1.4; }}
              .card {{ border:1px solid #ddd; border-radius:4px; margin-bottom:5px; box-shadow:0 2px 4px rgba(0,0,0,.1); }}
              .card-header {{ background:#f7f7f7; text-align:center; font-size:12px; font-weight:bold; padding:5px; }}
              .card-body {{ line-height:1.3; font-size:10px; }}
              table {{ border-collapse:collapse; width:100%; margin:0; }}
              th,td {{ border:1px solid #ddd; font-size:9px; padding:2px; line-height:1; text-align:left; }}
              th {{ background:#f1f1f1; font-weight:bold; }}
              .img-fluid {{ display:block; margin:auto; max-width:150px; height:auto; }}
            </style>
            </head>
            <body>
              {content_to_pdf}
            </body>
            </html>"""

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        filename = 'attachment; filename="ficha_medica_{}_{}.pdf"'.format(
            jugador_info["apellido"], jugador_info["nombre"]
        )
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = filename
        return response



    context = {
        'jugador_info': jugador_info,
        'registro_medico': registro_medico,
        'rol_usuario': rol_usuario,
        'ocultar_header': True,
        'qr_code': qr_code,
    }
    return render(request, 'medico/medico_views.html', context)

# Elimina la ficha Medica
def eliminar_ficha_medica(request, jugador_id):
    print("🔹 Iniciando eliminación de ficha médica...")

    # Obtener la ficha médica del jugador
    registro_medico = RegistroMedico.objects.filter(jugador__id=jugador_id).first()
    if not registro_medico:
        print("⚠️ No se encontró la ficha médica del jugador.")
        messages.error(request, "No se encontró la ficha médica del jugador.")
        return redirect('medico_home')

    print("✅ Ficha médica encontrada:", registro_medico)

    # Obtener el perfil del médico
    medico = Medico.objects.filter(profile=request.user.profile).first()
    if not medico:
        print("⚠️ No se encontró el perfil del médico asociado.")
        messages.error(request, "No se encontró el perfil del médico asociado.")
        return redirect('medico_home')

    rol_usuario = medico.profile.rol
    print(f"✅ Médico identificado: {medico}")
    print(f"🔍 Valor exacto de rol_usuario: {repr(rol_usuario)}")

    # Verificar permisos
    if rol_usuario.strip().lower() in ['médico', 'medico', 'administrador']:
        print("✅ Permiso concedido. Registrando eliminación...")

        # Guardar el registro en el modelo de EliminacionFichaMedica
        EliminacionFichaMedica.objects.create(
            jugador=f"{registro_medico.jugador.persona.profile.apellido} {registro_medico.jugador.persona.profile.nombre}",
            medico=f"{medico.profile.apellido} {medico.profile.nombre}",
            fecha_eliminacion=now()
        )

        # Eliminar la ficha médica
        registro_medico.delete()
        messages.success(request, "La ficha médica ha sido eliminada correctamente y registrada en el historial.")
        print("✅ Ficha médica eliminada con éxito y registrada.")
        return redirect('medico_home')
    else:
        print("⛔ No tienes permisos para eliminar esta ficha médica.")
        messages.error(request, "No tienes permisos para eliminar esta ficha médica.")
        return redirect('medico_home')








#################### VISTAS PARA LOS APTOS FISICOS GENERALES  ####################

class MedicoAptosGeneralesHomeView(ListView):
    model = AptoGeneral
    template_name = 'medico/medico_aptos_generales_home.html'
    context_object_name = 'aptos'

    # ===========================
    # QUERYSET PRINCIPAL
    # ===========================
    def get_queryset(self):
        search_dni = self.request.GET.get('search_dni', '').strip()
        search_name = self.request.GET.get('search_name', '').strip()
        estado = self.request.GET.get('estado', '').strip()

        # Sin filtros → no mostrar nada
        if not search_dni and not search_name and not estado:
            return AptoGeneral.objects.none()

        # 1️⃣ Resolver jugadores primero (CLAVE)
        jugadores_qs = Jugador.objects.select_related(
            'persona__profile'
        )

        if search_dni:
            if search_dni.isdigit() and len(search_dni) == 8:
                jugadores_qs = jugadores_qs.filter(
                    persona__profile__dni=search_dni
                )
            else:
                messages.error(self.request, "El DNI debe tener 8 números.")
                return AptoGeneral.objects.none()

        if search_name:
            palabras = search_name.split()
            if len(palabras) == 1:
                jugadores_qs = jugadores_qs.filter(
                    Q(persona__profile__nombre__icontains=palabras[0]) |
                    Q(persona__profile__apellido__icontains=palabras[0])
                )
            else:
                p1, p2 = palabras[0], palabras[1]
                jugadores_qs = jugadores_qs.filter(
                    Q(
                        persona__profile__nombre__icontains=p1,
                        persona__profile__apellido__icontains=p2
                    ) |
                    Q(
                        persona__profile__apellido__icontains=p1,
                        persona__profile__nombre__icontains=p2
                    )
                )

        # 2️⃣ Traer APTOS de esos jugadores
        qs = (
            AptoGeneral.objects
            .filter(jugador__in=jugadores_qs)
            .select_related(
                'jugador',
                'jugador__persona',
                'jugador__persona__profile',
                'actividad'
            )
            .order_by('-fecha_creacion')
        )

        if estado:
            qs = qs.filter(estado=estado)

        return qs

    # ===========================
    # CONTEXTO
    # ===========================
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtros visibles
        context['search_dni'] = self.request.GET.get('search_dni', '')
        context['search_name'] = self.request.GET.get('search_name', '')
        context['estado_filtro'] = self.request.GET.get('estado', '')

        # Perfil y médico
        profile_id = self.request.session.get("user_profile_id")
        profile = Profile.objects.filter(id=profile_id).first()
        medico = Medico.objects.filter(profile=profile).first() if profile else None

        context['profile'] = profile
        context['medico'] = medico

        # ===========================
        # RESUMEN (🔥 FIX DEFINITIVO)
        # ===========================
        hoy = timezone.localdate()

        qs_all = (
            AptoGeneral.objects
            .select_related(
                'jugador',
                'jugador__persona',
                'jugador__persona__profile'
            )
            .filter(jugador__persona__profile__isnull=False)
        )

        context["hoy"] = hoy
        context["pendientes_count"]     = qs_all.filter(estado="PENDIENTE").count()
        context["en_proceso_count"]     = qs_all.filter(estado="PROCESO").count()
        context["aprobadas_hoy_count"]  = qs_all.filter(estado="APROBADA").count()
        context["rechazadas_hoy_count"] = qs_all.filter(estado="RECHAZADA").count()

        # ===========================
        # TABLA
        # ===========================
        jugadores_info = []

        for apto in context.get('aptos', []):
            jugador = apto.jugador
            persona = jugador.persona if jugador else None
            profile = persona.profile if persona else None

            jugadores_info.append({
                'id': jugador.id if jugador else None,
                'dni': profile.dni if profile else "Sin DNI",
                'nombre': profile.nombre if profile else "Sin nombre",
                'apellido': profile.apellido if profile else "",
                'actividad': apto.actividad.nombre if apto.actividad else "Sin actividad",
                'estado': apto.estado,
                'fecha_creacion': apto.fecha_creacion,
                'fecha_caducidad': apto.fecha_caducidad,
                'consentimiento': apto.consentimiento_persona,
                'apto_id': apto.id,
                 
                'estudios': EstudiosAptoGeneral.objects.filter(apto=apto)
            })

        context['jugadores_info'] = jugadores_info
        return context

    # ===========================
    # POST – CARGA DE ESTUDIOS
    # ===========================
    def post(self, request, *args, **kwargs):
        jugador_id = request.POST.get('jugador_id')
        apto_id = request.POST.get('apto_id')
        form_saved = False

        form = EstudioAptoGeneralForm(request.POST, request.FILES)
        if form.is_valid():
            jugador = get_object_or_404(Jugador, id=jugador_id)
            apto = get_object_or_404(AptoGeneral, id=apto_id, jugador=jugador)

            estudio = form.save(commit=False)
            estudio.apto = apto
            estudio.save()

            messages.success(request, "✅ Estudio cargado exitosamente.")
            form_saved = True
        else:
            messages.error(request, "❌ Error al cargar el estudio.")

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['form_saved'] = form_saved
        context['jugador_id'] = jugador_id
        context['apto_id'] = apto_id

        return render(request, self.template_name, context)

def manejar_formulario_apto(request, jugador_id, apto_id, modelo, formulario_clase, template_name='medico/medico_aptos_generales_home.html'):

    print(f"🛠 Debug - jugador_id: {jugador_id}, apto_id: {apto_id} (Tipo: {type(apto_id)})")

    # Validar que apto_id sea int
    try:
        apto_id = int(apto_id)
    except ValueError:
        return HttpResponse("Error: apto_id debe ser un número entero.", status=400)

    # Obtener jugador y apto general
    jugador = get_object_or_404(Jugador, id=jugador_id)
    apto = get_object_or_404(AptoGeneral, id=apto_id, jugador=jugador)

    print(f"✅ Apto General encontrado: {apto}")

    # Buscar instancia del modelo relacionado con el apto
    instancia = modelo.objects.filter(apto=apto).first()

    if request.method == 'POST':
        formulario = formulario_clase(request.POST, request.FILES, instance=instancia)
        if formulario.is_valid():
            with transaction.atomic():
                instancia = formulario.save(commit=False)
                instancia.apto = apto
                instancia.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Formulario guardado exitosamente."})
    else:
        formulario = formulario_clase(instance=instancia)

    return render(request, template_name, {
        'jugador': jugador,
        f'{modelo.__name__.lower()}_form': formulario,
    })

def examen_fisico_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenFisicoGeneral, ExamenFisicoGeneralForm)

def examen_cardiovascular_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenCardiovascularGeneral, ExamenCardiovascularGeneralForm)

def examen_respiratorio_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenRespiratorioGeneral, ExamenRespiratorioGeneralForm)

def examen_abdomen_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenAbdomenGeneral, ExamenAbdomenGeneralForm)

def examen_genitourinario_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenGenitourinarioGeneral, ExamenGenitourinarioGeneralForm)

def examen_soma_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, ExamenSomaGeneral, ExamenSomaGeneralForm)

def motivo_actividad_general_view(request, jugador_id, apto_id):
    return manejar_formulario_apto(request, jugador_id, apto_id, MotivoActividadGeneral, MotivoActividadGeneralForm)




@login_required
def apto_general_update_view(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    jugador = apto.jugador

    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()
    medico = Medico.objects.filter(profile=profile).first() if profile else None

    estado_anterior = apto.estado

    if request.method == 'POST':
        apto_form = AptoGeneralForm(request.POST or None, instance=apto, medico=medico)
        estudio_form = EstudioAptoGeneralForm(request.POST, request.FILES)

        # ✅ Cargar Estudio
        if 'cargar_estudio' in request.POST:
            if estudio_form.is_valid():
                estudio = estudio_form.save(commit=False)
                estudio.apto = apto
                estudio.save()
                messages.success(request, "✅ Estudio cargado exitosamente.")
            else:
                messages.error(request, "❌ Error al cargar el estudio.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # 🗑️ Eliminar estudio
        elif 'eliminar_estudio' in request.POST:
            est_id = request.POST.get('estudio_id')
            if not est_id:
                messages.error(request, "❌ No se recibió el ID del estudio.")
                return redirect('apto_general_update_view', apto_id=apto.id)

            estudio = get_object_or_404(EstudiosAptoGeneral, pk=est_id, apto=apto)
            try:
                if estudio.archivo and hasattr(estudio.archivo, "path") and os.path.isfile(estudio.archivo.path):
                    os.remove(estudio.archivo.path)
            except Exception:
                pass
            estudio.delete()
            messages.success(request, "🗑️ Estudio eliminado correctamente.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen físico
        elif 'guardar_fisico' in request.POST:
            fisico_form = ExamenFisicoGeneralForm(
                request.POST,
                instance=ExamenFisicoGeneral.objects.filter(apto=apto).first()
                        or ExamenFisicoGeneral(apto=apto)
            )
            if fisico_form.is_valid():
                fisico_form.save()
                messages.success(request, "✅ Examen físico guardado.")
            else:
                messages.error(request, "❌ Error en examen físico.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen cardiovascular
        elif 'guardar_cardio' in request.POST:
            cardio_form = ExamenCardiovascularGeneralForm(
                request.POST, request.FILES,
                instance=ExamenCardiovascularGeneral.objects.filter(apto=apto).first()
                        or ExamenCardiovascularGeneral(apto=apto)
            )
            if cardio_form.is_valid():
                cardio_form.save()
                messages.success(request, "✅ Examen cardiovascular guardado.")
            else:
                messages.error(request, "❌ Error en examen cardiovascular.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen respiratorio
        elif 'guardar_respira' in request.POST:
            respira_form = ExamenRespiratorioGeneralForm(
                request.POST,
                instance=ExamenRespiratorioGeneral.objects.filter(apto=apto).first()
                        or ExamenRespiratorioGeneral(apto=apto)
            )
            if respira_form.is_valid():
                respira_form.save()
                messages.success(request, "✅ Examen respiratorio guardado.")
            else:
                messages.error(request, "❌ Error en examen respiratorio.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen abdomen
        elif 'guardar_abdomen' in request.POST:
            abdomen_form = ExamenAbdomenGeneralForm(
                request.POST,
                instance=ExamenAbdomenGeneral.objects.filter(apto=apto).first()
                        or ExamenAbdomenGeneral(apto=apto)
            )
            if abdomen_form.is_valid():
                abdomen_form.save()
                messages.success(request, "✅ Examen abdomen guardado.")
            else:
                messages.error(request, "❌ Error en examen abdomen.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen genitourinario
        elif 'guardar_genito' in request.POST:
            genito_form = ExamenGenitourinarioGeneralForm(
                request.POST,
                instance=ExamenGenitourinarioGeneral.objects.filter(apto=apto).first()
                        or ExamenGenitourinarioGeneral(apto=apto)
            )
            if genito_form.is_valid():
                genito_form.save()
                messages.success(request, "✅ Examen genitourinario guardado.")
            else:
                messages.error(request, "❌ Error en examen genitourinario.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar examen soma
        elif 'guardar_soma' in request.POST:
            soma_form = ExamenSomaGeneralForm(
                request.POST,
                instance=ExamenSomaGeneral.objects.filter(apto=apto).first()
                        or ExamenSomaGeneral(apto=apto)
            )
            if soma_form.is_valid():
                soma_form.save()
                messages.success(request, "✅ Examen soma guardado.")
            else:
                messages.error(request, "❌ Error en examen soma.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar motivo actividad
        elif 'guardar_motivo' in request.POST:
            motivo_form = MotivoActividadGeneralForm(
                request.POST,
                instance=MotivoActividadGeneral.objects.filter(apto=apto).first()
                        or MotivoActividadGeneral(apto=apto)
            )
            if motivo_form.is_valid():
                motivo_form.save()
                messages.success(request, "✅ Motivo de actividad guardado.")
            else:
                messages.error(request, "❌ Error en motivo de actividad.")
            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar sin aprobar
        elif 'guardar_apto' in request.POST:
            if apto_form.is_valid():
                with transaction.atomic():
                    registro = apto_form.save(commit=False)
                    registro.estado = registro.estado or estado_anterior
                    registro.medico = medico
                    registro.save()
                messages.success(request, "✅ Apto general actualizado.")
            else:
                messages.error(request, "❌ Error al aprobar el apto general.")

            return redirect('apto_general_update_view', apto_id=apto.id)

        # ✅ Guardar ficha (pendiente / aprobada / rechazada)
        elif 'guardar_ficha_completa' in request.POST:
            with transaction.atomic():
                if apto_form.is_valid():
                    registro = apto_form.save(commit=False)

                    estado_seleccionado = apto_form.cleaned_data.get("estado")

                    registro.medico = medico
                    registro.estado = estado_seleccionado
                    registro.save()

                    # 🔔 Enviar correo SOLO si se aprueba
                    if estado_seleccionado == "APROBADA":
                        try:
                            destinatario = (registro.jugador.persona.profile.user.email or "").strip()
                            fecha_venc = (
                                registro.fecha_caducidad.strftime("%d/%m/%Y")
                                if registro.fecha_caducidad else "sin definir"
                            )

                            asunto = "✅ Apto físico general aprobado"
                            cuerpo = f"""
        Hola {registro.jugador.persona.profile.nombre},

        Tu apto físico general ha sido aprobado.
        Fecha de vencimiento: {fecha_venc}.

        Ingresá a Checkeate para ver y descargar tu certificado:
        https://www.checkeate.com.ar

        ¡Gracias por confiar en Checkeate!
        """
                            enviar_correo(
                                asunto,
                                cuerpo,
                                [destinatario],
                                "notificaciones",
                                tipo="apto"
                            )
                        except Exception as e:
                            print(f"❌ Error al enviar correo de aprobación: {e}")

                        messages.success(request, "✅ Apto general aprobado correctamente.")

                    elif estado_seleccionado == "PENDIENTE":
                        messages.success(request, "🕒 Apto general guardado como pendiente.")

                    elif estado_seleccionado == "RECHAZADA":
                        messages.success(request, "❌ Apto general rechazado.")

                    # ⚡ Respuesta AJAX
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({"success": True})

                    return redirect('ficha_apto_general_view', apto_id=registro.id)

                else:
                    messages.error(request, "❌ Error al guardar el apto general.")

                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            "success": False,
                            "errors": apto_form.errors.as_json()
                        }, status=400)

                    return redirect('ficha_apto_general_view', apto_id=apto.id)


    else:
        # 🔹 Pasamos el médico logueado también en GET
        apto_form = AptoGeneralForm(instance=apto, medico=medico)
        estudio_form = EstudioAptoGeneralForm()

    estudios_qs = EstudiosAptoGeneral.objects.filter(apto=apto).order_by('-fecha_creacion')
    antecedente_instance = AntecedenteAptoGeneral.objects.filter(apto=apto).first()

    context = {
        'jugador': jugador,
        'profile': profile,
        'apto': apto,
        'apto_form': apto_form,
        'estudio_form': estudio_form,
        'antecedente': antecedente_instance,
        'antecedente_form': AntecedenteAptoGeneralForm(
            instance=antecedente_instance or AntecedenteAptoGeneral(apto=apto, jugador=jugador)
        ),
        'estudios_medicos': estudios_qs,
        'tipos_estudio': getattr(EstudiosAptoGeneral, "TIPO_ESTUDIO", ()),
        # forms
        'fisico_form': ExamenFisicoGeneralForm(instance=ExamenFisicoGeneral.objects.filter(apto=apto).first() or ExamenFisicoGeneral(apto=apto)),
        'cardiovascular_form': ExamenCardiovascularGeneralForm(instance=ExamenCardiovascularGeneral.objects.filter(apto=apto).first() or ExamenCardiovascularGeneral(apto=apto)),
        'respiratorio_form': ExamenRespiratorioGeneralForm(instance=ExamenRespiratorioGeneral.objects.filter(apto=apto).first() or ExamenRespiratorioGeneral(apto=apto)),
        'abdomen_form': ExamenAbdomenGeneralForm(instance=ExamenAbdomenGeneral.objects.filter(apto=apto).first() or ExamenAbdomenGeneral(apto=apto)),
        'genitourinario_form': ExamenGenitourinarioGeneralForm(instance=ExamenGenitourinarioGeneral.objects.filter(apto=apto).first() or ExamenGenitourinarioGeneral(apto=apto)),
        'soma_form': ExamenSomaGeneralForm(instance=ExamenSomaGeneral.objects.filter(apto=apto).first() or ExamenSomaGeneral(apto=apto)),
        'motivo_form': MotivoActividadGeneralForm(instance=MotivoActividadGeneral.objects.filter(apto=apto).first() or MotivoActividadGeneral(apto=apto)),
        'actividad': apto.actividad,
        'abrir': request.GET.get('abrir', ''),
    }

    return render(request, 'medico/cargar_apto_general.html', context)

@login_required
def ficha_apto_general_view(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)
    jugador = apto.jugador

    # Perfil del usuario que accede
    profile_id = request.session.get("user_profile_id")
    profile = Profile.objects.filter(id=profile_id).first()
    medico = Medico.objects.filter(profile=profile).first() if profile else None
    rol_usuario = profile.rol if profile else None

    # Antecedentes y estudios
    antecedentes = AntecedenteAptoGeneral.objects.filter(apto=apto).first()
    estudios = EstudiosAptoGeneral.objects.filter(apto=apto)

    # Secciones de examen
    fisico         = ExamenFisicoGeneral.objects.filter(apto=apto).first()
    cardio         = ExamenCardiovascularGeneral.objects.filter(apto=apto).first()
    respiratorio   = ExamenRespiratorioGeneral.objects.filter(apto=apto).first()
    abdomen        = ExamenAbdomenGeneral.objects.filter(apto=apto).first()
    genitourinario = ExamenGenitourinarioGeneral.objects.filter(apto=apto).first()
    soma           = ExamenSomaGeneral.objects.filter(apto=apto).first()
    motivo         = MotivoActividadGeneral.objects.filter(apto=apto).first()

    # Firma absoluta (para PDF)
    if apto.medico and apto.medico.firma:
        apto.medico.firma_url_abs = request.build_absolute_uri(apto.medico.firma.url)
    else:
        apto.medico.firma_url_abs = None

    # Info básica del jugador
    jugador_info = {
        'id': jugador.id,
        'edad': jugador.persona.profile.edad,
        'dni': jugador.persona.profile.dni,
        'nombre': jugador.persona.profile.nombre,
        'apellido': jugador.persona.profile.apellido,
        'direccion': jugador.persona.direccion,
        'telefono': jugador.persona.telefono,
        'grupo_sanguineo': jugador.grupo_sanguineo,
        'cobertura_medica': jugador.cobertura_medica,
        'numero_afiliado': jugador.numero_afiliado,
    }
     # ===================== QR =====================

    #qr_code = generar_qr(url_validacion)
    qr_code= generar_qr_certificado(request, "apto", apto.id)


    # Calcular categoría IMC (para vista y PDF)
    categoria_imc = None
    if fisico and fisico.imc:
        imc_val = float(fisico.imc)
        if imc_val < 18.5:
            categoria_imc = "Bajo peso"
        elif imc_val < 25:
            categoria_imc = "Peso normal"
        elif imc_val < 30:
            categoria_imc = "Sobrepeso"
        elif imc_val < 35:
            categoria_imc = "Obesidad grado I"
        elif imc_val < 40:
            categoria_imc = "Obesidad grado II"
        else:
            categoria_imc = "Obesidad grado III (mórbida)"
    else:
        categoria_imc = "-"

    # Contexto
    context = {
        'jugador_info': jugador_info,
        'apto': apto,
        'antecedentes': antecedentes,
        'estudios': estudios,
        'fisico': fisico,
        'cardio': cardio,
        'respiratorio': respiratorio,
        'abdomen': abdomen,
        'genitourinario': genitourinario,
        'soma': soma,
        'motivo': motivo,
        'rol_usuario': rol_usuario,
        'ocultar_header': True,
        'qr_code': qr_code,
        'categoria_imc': categoria_imc,
    }

    # ===================== PDF =====================
    if request.GET.get('descargar_pdf') == 'true':
        html_content = render_to_string('medico/ficha_apto_general.html', context)

        # Extraer solo <section id="content"> si lo usás en el template
        start_tag = '<section id="content">'
        end_tag = '</section>'
        content_start = html_content.find(start_tag)
        content_end = html_content.find(end_tag) + len(end_tag)
        if content_start != -1 and content_end != -1:
            content_to_pdf = html_content[content_start:content_end]
        else:
            content_to_pdf = html_content

        html_string = f"""<!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Apto General</title>
            </head>
            <body>
                {content_to_pdf}
            </body>
            </html>"""

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

        # CSS para PDF
        pdf_style_path = finders.find('core/css/pdf.css')
        stylesheets = [CSS(filename=pdf_style_path)] if pdf_style_path else []

        pdf = html.write_pdf(stylesheets=stylesheets)

        filename = f'attachment; filename="apto_general_{jugador_info["apellido"]}_{jugador_info["nombre"]}.pdf"'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = filename
        return response

    # ===================== HTML =====================
    return render(request, 'medico/ficha_apto_general.html', context)


# Descargar PDF si se solicita
    if request.GET.get('descargar_pdf') == 'true':
        html_content = render_to_string('medico/ficha_apto_general.html', context)

        # Extraer solo el bloque principal si lo envolvés en <section id="content">
        start_tag = '<section id="content">'
        end_tag = '</section>'
        content_start = html_content.find(start_tag)
        content_end = html_content.find(end_tag) + len(end_tag)
        content_to_pdf = html_content[content_start:content_end]

        html_string = f"""<!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Apto General</title>
            </head>
            <body>
                {content_to_pdf}
            </body>
            </html>"""

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

        # ✅ Buscar los archivos CSS con finders
        #bootstrap_path = finders.find('core/css/bootstrap.min.css')
        #custom_path = finders.find('core/css/style.css')
        pdf_style_path = finders.find('core/css/pdf.css')

        stylesheets = []
        #if bootstrap_path:
            #stylesheets.append(CSS(filename=bootstrap_path))
        #if custom_path:
            #stylesheets.append(CSS(filename=custom_path))
        if pdf_style_path:
            stylesheets.append(CSS(filename=pdf_style_path))

        # Generar PDF con los estilos encontrados
        pdf = html.write_pdf(stylesheets=stylesheets)

        filename = f'attachment; filename="apto_general_{jugador_info["apellido"]}_{jugador_info["nombre"]}.pdf"'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = filename
        return response



    return render(request, 'medico/ficha_apto_general.html', context)

class MedicoCargarEstudiosView(View):
    template_name = 'medico/cargar_estudios_dni.html'

    def get(self, request):
        dni = request.GET.get('dni', '').strip()
        jugador = None
        apto_vigente = None
        form = EstudioAptoGeneralForm()

        if dni and dni.isdigit() and len(dni) == 8:
            jugador = (
                Jugador.objects
                .filter(persona__profile__dni=dni)
                .select_related('persona__profile')
                .first()
            )

            if jugador:
                apto_vigente = (
                    AptoGeneral.objects
                    .filter(jugador=jugador)
                    .order_by('-fecha_creacion')
                    .first()
                )
            else:
                messages.error(request, "No se encontró un jugador con ese DNI.")
        elif dni:
            messages.error(request, "El DNI debe tener 8 números.")

        return render(request, self.template_name, {
            'dni': dni,
            'jugador': jugador,
            'apto': apto_vigente,
            'form': form,
            'form_saved': False,
        })

    def post(self, request):
        dni = request.POST.get('dni')
        jugador = get_object_or_404(
            Jugador,
            persona__profile__dni=dni
        )

        apto_id = request.POST.get('apto_id')
        apto = None

        if apto_id:
            apto = get_object_or_404(
                AptoGeneral,
                id=apto_id,
                jugador=jugador
            )

        form = EstudioAptoGeneralForm(request.POST, request.FILES)

        if form.is_valid():
            estudio = form.save(commit=False)
            estudio.apto = apto  # ✔ asociación correcta
            estudio.save()

            return render(request, self.template_name, {
                'dni': dni,
                'jugador': jugador,
                'apto': apto,
                'form': EstudioAptoGeneralForm(),  # limpio
                'form_saved': True,  # 🔥 ESTA ES LA CLAVE DEL MODAL
            })

        messages.error(request, "❌ Error al cargar el estudio.")
        return render(request, self.template_name, {
            'dni': dni,
            'jugador': jugador,
            'apto': apto,
            'form': form,
            'form_saved': False,
        })


#################### VISTAS PARA EL CUS DE LOS ESTUDIANTES ####################

#vista cus_home

class CusHomeView(LoginRequiredMixin, ListView):

    model = Estudiante
    template_name = 'medico/cus_home.html'
    context_object_name = 'estudiantes'

    def get_queryset(self):
        queryset = Estudiante.objects.all()
        search_dni = self.request.GET.get('search_dni', '').strip()
        search_name = self.request.GET.get('search_name', '').strip()

        if not search_dni and not search_name:
            return Estudiante.objects.none()

        if search_dni:
            if search_dni.isdigit() and len(search_dni) == 8:
                queryset = queryset.filter(dni__icontains=search_dni)
            else:
                messages.error(self.request, "El DNI ingresado debe contener exactamente 8 números.")
                return Estudiante.objects.none()

        if search_name:
            palabras = search_name.split()
            consulta = Q()

            if len(palabras) == 1:
                consulta = Q(nombre__icontains=palabras[0]) | Q(apellido__icontains=palabras[0])
            elif len(palabras) >= 2:
                primer = palabras[0]
                segundo = palabras[1]
                consulta = (Q(nombre__icontains=primer) & Q(apellido__icontains=segundo)) | \
                           (Q(nombre__icontains=segundo) & Q(apellido__icontains=primer))

            queryset = queryset.filter(consulta)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_dni'] = self.request.GET.get('search_dni', '')
        context['search_name'] = self.request.GET.get('search_name', '')

        profile_id = self.request.session.get("user_profile_id")
        profile = Profile.objects.filter(id=profile_id).first()
        context['profile'] = profile

        if profile:
            context['medico'] = Medico.objects.filter(profile=profile).first()
        else:
            context['medico'] = None

        estudiantes_info = []

        if 'estudiantes' in context and context['estudiantes'].exists():
            for estudiante in context['estudiantes']:

                cus = Cus.objects.filter(estudiante=estudiante).order_by('-id').first()

                info = {
                    'id': estudiante.id,
                    'dni': estudiante.dni,
                    'nombre': estudiante.nombre,
                    'apellido': estudiante.apellido,
                    'colegio': estudiante.colegio_activo(),
                    'estado': cus.estado if cus else 'Sin ficha',
                    'cus_id': cus.id if cus else None,
                    'tutor': f"{estudiante.tutor.profile.nombre} {estudiante.tutor.profile.apellido}" if estudiante.tutor else 'Sin tutor',
                }

                estudiantes_info.append(info)

        context['estudiantes_info'] = estudiantes_info
        context['cus_form'] = CusForm()

        return context


#Funcion para calcular la edad
def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

# vista para cargar_cus
@login_required
def cus_update_view(request, cus_id):
    cus = get_object_or_404(Cus, id=cus_id)
    estudiante = cus.estudiante
    cus_form = CusForm(instance=cus)
    estudio_form = EstudioCusForm()
    actualizaciones_qs = cus.actualizaciones.all()
    cantidad_actualizaciones = actualizaciones_qs.count()

    # Verificar si el CUS está vencido
    vencido = cus.fecha_caducidad and cus.fecha_caducidad < date.today()
    print(f"Vencido : ", vencido)

    if vencido and cantidad_actualizaciones >= 5:
        cus.estado = "VENCIDO"
        cus.save()
        messages.warning(request, "❌ El CUS ha sido marcado como vencido tras 5 actualizaciones.")

    actualizacion_form = None
    if vencido and cantidad_actualizaciones < 5:
        actualizacion_form = ActualizacionCUSForm(
            request.POST or None,
            initial={
                'edad': calcular_edad(estudiante.fecha_nacimiento),
                'lugar': getattr(estudiante, 'lugar_nacimiento', '')
            }
        )

    antecedentes = AntecedentesCUS.objects.filter(estudiante=estudiante).order_by('-id').first()
    if request.method == 'POST':
        print("📥 request.POST:", request.POST)

        if 'guardar_examenes_medicos' in request.POST:
            forms_valid = True
            form_instances = {
                'examen_fisico_form': ExamenFisicoForm(request.POST, instance=ExamenFisico.objects.filter(cus=cus).first() or ExamenFisico(cus=cus)),
                'alimentacion_form': AlimentacionNutricionForm(request.POST, instance=AlimentacionNutricion.objects.filter(cus=cus).first() or AlimentacionNutricion(cus=cus)),
                'oftalmologico_form': ExamenOftalmologicoForm(request.POST, instance=ExamenOftalmologico.objects.filter(cus=cus).first() or ExamenOftalmologico(cus=cus)),
                'fono_form': ExamenFonoaudiologicoForm(request.POST, instance=ExamenFonoaudiologico.objects.filter(cus=cus).first() or ExamenFonoaudiologico(cus=cus)),
                'piel_form': ExamenPielForm(request.POST, instance=ExamenPiel.objects.filter(cus=cus).first() or ExamenPiel(cus=cus)),
                'odonto_form': ExamenOdontologicoForm(request.POST, instance=ExamenOdontologico.objects.filter(cus=cus).first() or ExamenOdontologico(cus=cus)),
                'cardio_form': ExamenCardiovascularForm(request.POST, instance=ExamenCardiovascular.objects.filter(cus=cus).first() or ExamenCardiovascular(cus=cus)),
                'respiratorio_form': ExamenRespiratorioForm(request.POST, instance=ExamenRespiratorio.objects.filter(cus=cus).first() or ExamenRespiratorio(cus=cus)),
                'abdomen_form': ExamenAbdomenForm(request.POST, instance=ExamenAbdomen.objects.filter(cus=cus).first() or ExamenAbdomen(cus=cus)),
                'genito_form': ExamenGenitourinarioForm(request.POST, instance=ExamenGenitourinario.objects.filter(cus=cus).first() or ExamenGenitourinario(cus=cus)),
                'endocrino_form': ExamenEndocrinologicoForm(request.POST, instance=ExamenEndocrinologico.objects.filter(cus=cus).first() or ExamenEndocrinologico(cus=cus)),
                'osteo_form': ExamenOsteoarticularForm(request.POST, instance=ExamenOsteoarticular.objects.filter(cus=cus).first() or ExamenOsteoarticular(cus=cus)),
                'neuro_form': ExamenNeurologicoForm(request.POST, instance=ExamenNeurologico.objects.filter(cus=cus).first() or ExamenNeurologico(cus=cus)),
                'comentario_form': ComentarioDerivacionForm(request.POST, instance=ComentarioDerivacion.objects.filter(cus=cus).first() or ComentarioDerivacion(cus=cus)),
                'recomendaciones_form': RecomendacionesForm(request.POST, instance=Recomendaciones.objects.filter(cus=cus).first() or Recomendaciones(cus=cus)),
            }

            for name, form in form_instances.items():
                if form.is_valid():
                    form.save()
                    print(f"✅ Guardado: {name}")
                else:
                    forms_valid = False
                    print(f"❌ Errores en {name}:", form.errors)

            if forms_valid:
                messages.success(request, "✅ Exámenes médicos guardados correctamente.")
                return redirect('cus_update_view', cus_id=cus.id)
            else:
                messages.warning(request, "⚠️ Algunos exámenes tienen errores. Revisá los datos.")
                context.update(form_instances)
                return render(request, 'medico/cargar_cus.html', context)

        elif 'guardar_actualizacion' in request.POST:
            if cantidad_actualizaciones >= 5:
                messages.error(request, "⚠️ No se pueden registrar más de 5 actualizaciones.")
                return redirect('cus_update_view', cus_id=cus.id)

            actualizacion_form = ActualizacionCUSForm(request.POST)
            if actualizacion_form.is_valid():
                actualizacion = actualizacion_form.save(commit=False)
                actualizacion.cus = cus
                actualizacion.edad = calcular_edad(estudiante.fecha_nacimiento)

                profile_id = request.session.get("user_profile_id")
                if profile_id:
                    profile = Profile.objects.filter(id=profile_id).first()
                    if profile:
                        medico = Medico.objects.filter(profile=profile).first()
                        if medico:
                            actualizacion.medico = medico

                if actualizacion.peso and actualizacion.talla:
                    altura_m = float(actualizacion.talla) / 100
                    imc = float(actualizacion.peso) / (altura_m ** 2)
                    actualizacion.imc = round(imc, 2)
                    if imc < 18.5:
                        actualizacion.diagnostico_antropometrico = "Bajo peso"
                    elif 18.5 <= imc <= 24.9:
                        actualizacion.diagnostico_antropometrico = "Normal"
                    elif 25 <= imc <= 29.9:
                        actualizacion.diagnostico_antropometrico = "Sobrepeso"
                    elif 30 <= imc <= 34.9:
                        actualizacion.diagnostico_antropometrico = "Obesidad grado I"
                    elif 35 <= imc <= 39.9:
                        actualizacion.diagnostico_antropometrico = "Obesidad grado II"
                    else:
                        actualizacion.diagnostico_antropometrico = "Obesidad grado III"

                actualizacion.vencimiento = date(date.today().year + 1, 1, 1)
                actualizacion.save()
                cus.estado = "APROBADA"
                cus.save()
                messages.success(request, "✅ Actualización guardada y CUS aprobado.")
                return redirect('cus_views', cus_id=cus.id)

        elif 'cargar_estudio' in request.POST:
            estudio_form = EstudioCusForm(request.POST, request.FILES)
            if estudio_form.is_valid():
                estudio = estudio_form.save(commit=False)
                estudio.cus = cus
                estudio.save()
                messages.success(request, "✅ Estudio cargado exitosamente.")
            else:
                messages.error(request, "❌ Error al cargar el estudio.")
            return redirect('cus_update_view')

        # ✅ Guardar ficha CUS y aprobar
        elif 'guardar_ficha_cus' in request.POST:
            campos_requeridos = [
                ExamenFisico, AlimentacionNutricion, ExamenOftalmologico,
                ExamenFonoaudiologico, ExamenPiel, ExamenOdontologico,
                ExamenCardiovascular, ExamenRespiratorio, ExamenAbdomen,
                ExamenGenitourinario, ExamenEndocrinologico, ExamenOsteoarticular,
                ExamenNeurologico, ComentarioDerivacion, Recomendaciones
            ]
            faltantes = [modelo.__name__ for modelo in campos_requeridos if not modelo.objects.filter(cus=cus).exists()]

            if faltantes:
                messages.error(request, f"❌ No se puede guardar el CUS. Faltan completar: {', '.join(faltantes)}")
                return redirect('cus_update_view', cus_id=cus.id)

            with transaction.atomic():
                cus_form = CusForm(request.POST, instance=cus)
                antecedentes = AntecedentesCUS.objects.filter(estudiante=estudiante).first()
                if not antecedentes:
                    antecedentes = AntecedentesCUS(estudiante=estudiante)
                    antecedentes.save()

                if cus_form.is_valid():
                    cus = cus_form.save(commit=False)
                    cus.estado = "APROBADA"
                    if cus.fecha_de_llenado:
                        cus.fecha_caducidad = date(cus.fecha_de_llenado.year + 1, 1, 1)
                    cus.save()

                    # 🔔 Enviar correo solo una vez
                    try:
                        destinatario = (estudiante.email or "").strip()
                        asunto = "✅ Certificado Único de Salud (CUS) aprobado"
                        cuerpo = f"""
                        Hola {estudiante.nombre} {estudiante.apellido},

                        Tu Certificado Único de Salud (CUS) ha sido aprobado exitosamente.

                        Fecha de caducidad: {cus.fecha_caducidad.strftime('%d/%m/%Y') if cus.fecha_caducidad else "sin definir"}.

                        Ingresá a Checkeate para descargar o consultar tu certificado:
                        https://www.checkeate.com.ar

                        ¡Gracias por confiar en Checkeate!
                        """
                        enviar_correo(asunto, cuerpo, [destinatario], "notificaciones", tipo="cus")
                    except Exception as e:
                        print(f"❌ Error al enviar correo CUS: {e}")

                    messages.success(request, "✅ Certificado CUS guardado y aprobado correctamente.")
                else:
                    messages.error(request, "❌ Error al guardar el certificado CUS.")

            return redirect('cus_home')

    context = {
        'cus': cus,
        'estudiante': estudiante,
        'cus_form': cus_form,
        'estudio_cus_form': estudio_form,
        'antecedentes': antecedentes,
        'nombre': estudiante.nombre,
        'apellido': estudiante.apellido,
        'dni': estudiante.dni,
        'edad': estudiante.fecha_nacimiento,
        'tutor': f"{estudiante.tutor.profile.nombre} {estudiante.tutor.profile.apellido}" if estudiante.tutor else "-",
        'colegio': estudiante.colegio_activo(),
        'examen_fisico_form': ExamenFisicoForm(instance=ExamenFisico.objects.filter(cus=cus).first()),
        'alimentacion_form': AlimentacionNutricionForm(instance=AlimentacionNutricion.objects.filter(cus=cus).first()),
        'oftalmologico_form': ExamenOftalmologicoForm(instance=ExamenOftalmologico.objects.filter(cus=cus).first()),
        'fono_form': ExamenFonoaudiologicoForm(instance=ExamenFonoaudiologico.objects.filter(cus=cus).first()),
        'piel_form': ExamenPielForm(instance=ExamenPiel.objects.filter(cus=cus).first()),
        'odonto_form': ExamenOdontologicoForm(instance=ExamenOdontologico.objects.filter(cus=cus).first()),
        'cardio_form': ExamenCardiovascularForm(instance=ExamenCardiovascular.objects.filter(cus=cus).first()),
        'respiratorio_form': ExamenRespiratorioForm(instance=ExamenRespiratorio.objects.filter(cus=cus).first()),
        'abdomen_form': ExamenAbdomenForm(instance=ExamenAbdomen.objects.filter(cus=cus).first()),
        'genito_form': ExamenGenitourinarioForm(instance=ExamenGenitourinario.objects.filter(cus=cus).first()),
        'endocrino_form': ExamenEndocrinologicoForm(instance=ExamenEndocrinologico.objects.filter(cus=cus).first()),
        'osteo_form': ExamenOsteoarticularForm(instance=ExamenOsteoarticular.objects.filter(cus=cus).first()),
        'neuro_form': ExamenNeurologicoForm(instance=ExamenNeurologico.objects.filter(cus=cus).first()),
        'comentario_form': ComentarioDerivacionForm(instance=ComentarioDerivacion.objects.filter(cus=cus).first()),
        'recomendaciones_form': RecomendacionesForm(instance=Recomendaciones.objects.filter(cus=cus).first()),
        'actualizacion_form': actualizacion_form,
        'vencido': vencido,
        'actualizaciones': cus.actualizaciones.all()
    }
    if vencido and actualizacion_form is None:
        messages.error(request, "No se pudo generar el formulario de actualización. Contacte a soporte.")
        return redirect('cus_home')
    return render(request, 'medico/cargar_cus.html', context)




# Manejo genérico para formularios del CUS


def manejar_formulario_cus(request, estudiante_id, cus_id, modelo, formulario_clase, template_name='medico/cargar_cus.html'):
    try:
        cus_id = int(cus_id)
    except ValueError:
        return HttpResponse("Error: cus_id debe ser un número entero.", status=400)

    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    cus = get_object_or_404(Cus, id=cus_id, estudiante=estudiante)

    instancia = modelo.objects.filter(cus=cus).first()

    if request.method == 'POST':
        formulario = formulario_clase(request.POST, request.FILES, instance=instancia)
        if formulario.is_valid():
            with transaction.atomic():
                instancia = formulario.save(commit=False)
                instancia.cus = cus
                instancia.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Formulario guardado exitosamente."})
    else:
        formulario = formulario_clase(instance=instancia)

    return render(request, template_name, {
        'estudiante': estudiante,
        f'{modelo.__name__.lower()}_form': formulario,
    })

# Vistas específicas para cada formulario del CUS
def examen_fisico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenFisico, ExamenFisicoForm)

def alimentacion_nutricion_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, AlimentacionNutricion, AlimentacionNutricionForm)

def examen_oftalmologico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenOftalmologico, ExamenOftalmologicoForm)

def examen_fonoaudiologico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenFonoaudiologico, ExamenFonoaudiologicoForm)

def examen_piel_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenPiel, ExamenPielForm)

def examen_odontologico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenOdontologico, ExamenOdontologicoForm)

def examen_cardiovascular_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenCardiovascular, ExamenCardiovascularForm)

def examen_respiratorio_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenRespiratorio, ExamenRespiratorioForm)

def examen_abdomen_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenAbdomen, ExamenAbdomenForm)

def examen_genitourinario_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenGenitourinario, ExamenGenitourinarioForm)

def examen_endocrinologico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenEndocrinologico, ExamenEndocrinologicoForm)

def examen_osteoarticular_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenOsteoarticular, ExamenOsteoarticularForm)

def examen_neurologico_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ExamenNeurologico, ExamenNeurologicoForm)

def estudio_cus_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, EstudioCus, EstudioCusForm)

def comentario_derivacion_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, ComentarioDerivacion, ComentarioDerivacionForm)

def recomendaciones_view(request, estudiante_id, cus_id):
    return manejar_formulario_cus(request, estudiante_id, cus_id, Recomendaciones, RecomendacionesForm)

#Registro del cus con sus formularios
@login_required
def cus_form_view(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    cus = Cus.objects.filter(estudiante=estudiante).first()
    if not cus:
        cus = Cus(estudiante=estudiante)

    if request.method == 'POST':
        form = CusForm(request.POST, instance=cus)
        if form.is_valid():
            instance = form.save(commit=False)
            #Cargamos la fecha de caducidad automatica
            if not instance.fecha_de_llenado:
                instance.fecha_de_llenado = date.today()

                # Establecer fecha de caducidad: 1 de enero del año siguiente
                instance.fecha_caducidad = date(instance.fecha_de_llenado.year + 1, 1, 1)
            # Asociar médico logueado si no está
            profile_id = request.session.get("user_profile_id")
            if profile_id and not instance.medico:
                from core.models import Profile
                from Medico.models import Medico
                profile = Profile.objects.filter(id=profile_id).first()
                if profile:
                    medico = Medico.objects.filter(profile=profile).first()
                    if medico:
                        instance.medico = medico

            instance.save()
            messages.success(request, "✅ Datos personales del CUS guardados correctamente.")

            # 👇 Verificamos qué botón se presionó
            if 'guardar_ficha_completa' in request.POST:
                return redirect('cus_home')  # redirige al home del médico

            return redirect('cus_update_view', cus_id=cus.id)
    else:
        form = CusForm(instance=cus)

    return render(request, 'medico/cus_form.html', {
        'form': form,
        'estudiante': estudiante
    })

# Arma la vista finaal del cus y la posibilidad de descargarlo en Pdf
@login_required
def cus_views(request, cus_id):
    cus = get_object_or_404(Cus, id=cus_id)
    estudiante = cus.estudiante
    examenes = {
        'Examen Físico': ExamenFisico.objects.filter(cus=cus).first(),
        'Alimentación y Nutrición': AlimentacionNutricion.objects.filter(cus=cus).first(),
        'Oftalmológico': ExamenOftalmologico.objects.filter(cus=cus).first(),
        'Fonoaudiológico': ExamenFonoaudiologico.objects.filter(cus=cus).first(),
        'Piel': ExamenPiel.objects.filter(cus=cus).first(),
        'Odontológico': ExamenOdontologico.objects.filter(cus=cus).first(),
        'Cardiovascular': ExamenCardiovascular.objects.filter(cus=cus).first(),
        'Respiratorio': ExamenRespiratorio.objects.filter(cus=cus).first(),
        'Abdomen': ExamenAbdomen.objects.filter(cus=cus).first(),
        'Genitourinario': ExamenGenitourinario.objects.filter(cus=cus).first(),
        'Endocrinológico': ExamenEndocrinologico.objects.filter(cus=cus).first(),
        'Osteoarticular': ExamenOsteoarticular.objects.filter(cus=cus).first(),
        'Neurológico': ExamenNeurologico.objects.filter(cus=cus).first(),
        'Comentario': ComentarioDerivacion.objects.filter(cus=cus).first(),
        'Recomendaciones': Recomendaciones.objects.filter(cus=cus).first(),
    }

    for nombre, instancia in examenes.items():
        if instancia:
            print(f"✅ {nombre}: {instancia}")
        else:
            print(f"❌ {nombre}: No se encontró instancia")

    profile_id = request.session.get("user_profile_id")
    perfil = None
    if profile_id:
        perfil = Profile.objects.filter(id=profile_id).first()
    qr_img = generar_qr_certificado(request, "cus", cus.id)
    contexto = {
        'perfil': perfil,
        'cus': cus,
        'estudiante': estudiante,
        'tutor': f"{estudiante.tutor.profile.nombre} {estudiante.tutor.profile.apellido}" if estudiante.tutor else "-",
        'colegio': estudiante.colegio_activo(),
        'antecedentes': getattr(estudiante, 'antecedentes', None),
        'examen_fisico_form': ExamenFisicoForm(instance=ExamenFisico.objects.filter(cus=cus).first()),
        'alimentacion_form': AlimentacionNutricionForm(instance=AlimentacionNutricion.objects.filter(cus=cus).first()),
        'oftalmologico_form': ExamenOftalmologicoForm(instance=ExamenOftalmologico.objects.filter(cus=cus).first()),
        'fono_form': ExamenFonoaudiologicoForm(instance=ExamenFonoaudiologico.objects.filter(cus=cus).first() or ExamenFonoaudiologico(cus=cus)),
        'piel_form': ExamenPielForm(instance=ExamenPiel.objects.filter(cus=cus).first() or ExamenPiel(cus=cus)),
        'odonto_form': ExamenOdontologicoForm(instance=ExamenOdontologico.objects.filter(cus=cus).first() or ExamenOdontologico(cus=cus)),
        'cardio_form': ExamenCardiovascularForm(instance=ExamenCardiovascular.objects.filter(cus=cus).first() or ExamenCardiovascular(cus=cus)),
        'respiratorio_form': ExamenRespiratorioForm(instance=ExamenRespiratorio.objects.filter(cus=cus).first() or ExamenRespiratorio(cus=cus)),
        'abdomen_form': ExamenAbdomenForm(instance=ExamenAbdomen.objects.filter(cus=cus).first() or ExamenAbdomen(cus=cus)),
        'genito_form': ExamenGenitourinarioForm(instance=ExamenGenitourinario.objects.filter(cus=cus).first() or ExamenGenitourinario(cus=cus)),
        'endocrino_form': ExamenEndocrinologicoForm(instance=ExamenEndocrinologico.objects.filter(cus=cus).first() or ExamenEndocrinologico(cus=cus)),
        'osteo_form': ExamenOsteoarticularForm(instance=ExamenOsteoarticular.objects.filter(cus=cus).first() or ExamenOsteoarticular(cus=cus)),
        'neuro_form': ExamenNeurologicoForm(instance=ExamenNeurologico.objects.filter(cus=cus).first() or ExamenNeurologico(cus=cus)),
        'comentario_form': ComentarioDerivacionForm(instance=ComentarioDerivacion.objects.filter(cus=cus).first() or ComentarioDerivacion(cus=cus)),
        'recomendaciones_form': RecomendacionesForm(instance=Recomendaciones.objects.filter(cus=cus).first() or Recomendaciones(cus=cus)),
        'qr_img': qr_img,
        'actualizaciones': cus.actualizaciones.all()
    }

    if request.GET.get('descargar_pdf') == 'true':
        html = render_to_string("medico/cus_pdf.html", contexto)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cus_{estudiante.apellido}_{estudiante.nombre}.pdf"'
        return response

    return render(request, 'medico/cus_views.html', contexto)

def extraer_y_validar_qr(file_obj):
    try:
        file_obj.seek(0)  # 🔑 IMPORTANTE
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")

        for i, page in enumerate(doc):
            print(f"[DEBUG] Procesando página {i + 1}")

            # 🔥 DPI alto para mejor detección
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            qrs = decode(image)
            print(f"[DEBUG] QRs detectados: {len(qrs)}")

            if qrs:
                # ✅ HAY QR → APROBADO (sin importar contenido)
                data = qrs[0].data.decode("utf-8", errors="ignore")
                print(f"[DEBUG] QR detectado (aprobado): {data}")

                return {
                    "valido": True,
                    "contenido": data
                }

        print("[DEBUG] No se detectó ningún QR en el PDF")
        return {"valido": False}

    except Exception as e:
        print(f"[ERROR] Error general QR: {e}")
        return {"valido": False}

def verificar_qr_pdf(request):
    if request.method == "POST" and request.FILES.get("file"):
        archivo = request.FILES["file"]

        try:
            archivo.seek(0)
            doc = fitz.open(stream=archivo.read(), filetype="pdf")

            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

                qrs = decode(image)

                if qrs:
                    data = qrs[0].data.decode("utf-8", errors="ignore")

                    return JsonResponse({
                        "valido": True,
                        "contenido": data
                    })

            # ❌ No hay QR
            return JsonResponse({"valido": False})

        except Exception as e:
            print(f"[ERROR] Verificación QR fallida: {e}")
            return JsonResponse({"valido": False})

    return JsonResponse({"valido": False})

# Funcion para cargar documentacion del medico
@login_required
def cargar_documentacion(request):
    profile_id = request.session.get("user_profile_id")
    if not profile_id:
        messages.error(request, "No se encontró un perfil activo. Iniciá sesión nuevamente.")
        return redirect("login")

    try:
        profile = Profile.objects.get(id=profile_id, rol="medico")
    except Profile.DoesNotExist:
        messages.error(request, "Tu perfil activo no es médico o no existe.")
        return redirect("select_role")

    medico, _ = Medico.objects.get_or_create(profile=profile)
    doc, _ = Documentos.objects.get_or_create(medico=medico)

    if request.method == 'POST':
        print("FILES ENVIADOS:", request.FILES)
        form_doc = DocumentosForm(request.POST, request.FILES, instance=doc)
        form_medico = MedicoDatosComplementariosForm(request.POST, instance=medico)

        archivo_matricula = request.FILES.get("certificado_matricula")
        archivo_firma = request.FILES.get("certificado_firma_electronica")
        contrato_aceptado = request.POST.get("contrato_aceptado") == "on"

        if not contrato_aceptado:
            form_doc.add_error("contrato_aceptado", "Debe aceptar los términos del contrato para continuar.")
        if not archivo_matricula:
            form_doc.add_error("certificado_matricula", "Debe subir el certificado de matrícula.")
        if not archivo_firma:
            form_doc.add_error("certificado_firma_electronica", "Debe subir el certificado de firma electrónica.")



        if form_doc.is_valid() and form_medico.is_valid() and contrato_aceptado and archivo_matricula and archivo_firma:
            resultado = extraer_y_validar_qr(archivo_matricula)
            if resultado and resultado.get("valido"):
                form_medico.save()
                doc.certificado_matricula = archivo_matricula
                doc.certificado_firma_electronica = archivo_firma
                doc.url_certificado = resultado.get("contenido", "")
                doc.qr_valido = True
                doc.contrato_aceptado = True
                doc.save()
                # Copiamos la firma al modelo Medico también
                medico.firma = archivo_firma
                medico.save()


                print(f"[DEBUG] Documentación válida guardada correctamente.")
                return redirect('seleccionar_apto')
            else:
                form_doc.add_error("certificado_matricula", "El QR no es válido. Verifique el documento.")
                print("[DEBUG] Certificado de matrícula con QR inválido.")
    else:
        form_doc = DocumentosForm(instance=doc)
        form_medico = MedicoDatosComplementariosForm(instance=medico)

    return render(request, 'medico/cargar_documentacion.html', {
        'form': form_doc,
        'form_medico': form_medico,
        'doc': doc,
        'profile': profile
    })


#Vista del contrato del medico
def contrato (request):
    return render(request, 'medico/contrato.html')

# Vista para generar un codico qr para verificacion de validez

"""def generar_qr(data: str):

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{qr_b64}"

    def validar_apto_general_view(request, apto_id):
    apto = get_object_or_404(AptoGeneral, id=apto_id)

    jugador = apto.jugador
    jugador_info = {
        "nombre": jugador.persona.profile.nombre,
        "apellido": jugador.persona.profile.apellido,
        "dni": jugador.persona.profile.dni,
    }

    context = {
        "apto": apto,
        "jugador_info": jugador_info,
    }
    return render(request, "medico/validar_apto.html", context)






    """


def generar_qr_certificado(request, tipo: str, id_certificado: int):
    """
    Genera un QR base64 válido para cualquier tipo de certificado:
    tipo = 'apto', 'registro' o 'cus'
    """
    url = request.build_absolute_uri(reverse('validar_certificado', args=[tipo, id_certificado]))

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{qr_b64}"

def validar_certificado_view(request, tipo, id_certificado):
    """
    Vista unificada para validar certificados QR de:
    - Apto General
    - Registro Médico (torneos/competencias)
    - CUS (Certificado Único de Salud)
    """
    template = "medico/validar_apto.html"
    if tipo == "apto":
        certificado = get_object_or_404(AptoGeneral, id=id_certificado)
        context = {
            "titulo": "Apto Físico General",
            "jugador": certificado.jugador,
            "fecha": certificado.fecha_creacion,
            "estado": certificado.estado,
            "fecha_caducidad": certificado.fecha_caducidad,
        }

    elif tipo == "registro":
        certificado = get_object_or_404(RegistroMedico, id=id_certificado)
        context = {
            "titulo": "Registro Médico Torneo",
            "jugador": certificado.jugador,
            "medico": certificado.medico,
            "fecha": certificado.fecha_creacion,
            "estado": certificado.estado,
            "fecha_caducidad": certificado.fecha_caducidad,
        }

    elif tipo == "cus":
        certificado = get_object_or_404(Cus, id=id_certificado)
        context = {
            "titulo": "Certificado Único de Salud (CUS)",
            "estudiante": certificado.estudiante,
            "medico": certificado.medico,
            "fecha": certificado.fecha_creacion,
            "estado": certificado.estado,
            "fecha_caducidad": certificado.fecha_caducidad,
        }

    else:
        raise Http404("Tipo de certificado no reconocido.")

    return render(request, template, context)




def buscar_apto_general_view(request):
    mensaje = None
    if request.method == "POST":
        apto_id = request.POST.get("apto_id")
        dni = request.POST.get("dni")

        if apto_id:
            return redirect("validar_apto_general", apto_id=apto_id)

        if dni:
            jugador = Jugador.objects.filter(persona__profile__dni=dni).first()
            if jugador:
                apto = AptoGeneral.objects.filter(jugador=jugador).last()
                if apto:
                    return redirect("validar_apto_general", apto_id=apto.id)
                else:
                    mensaje = "El jugador existe pero no tiene aptos cargados."
            else:
                mensaje = "No se encontró ningún jugador con ese DNI."

    return render(request, "medico/buscar_apto.html", {"mensaje": mensaje})

from .models import ObservacionPersona
from .forms import ObservacionPersonaForm
from django.views.generic import TemplateView

class MedicoObservacionesPersonaView(LoginRequiredMixin, TemplateView):
    template_name = "medico/observaciones_persona.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        dni = self.request.GET.get("dni")
        context["dni"] = dni
        context["form"] = ObservacionPersonaForm()

        if dni and dni.isdigit():
            persona = Persona.objects.filter(
                profile__dni=dni
            ).select_related("profile").first()

            context["persona"] = persona

            if persona:
                context["observaciones"] = (
                    ObservacionPersona.objects
                    .filter(persona=persona)
                )

        return context

    def post(self, request, *args, **kwargs):
        persona_id = request.POST.get("persona_id")
        persona = get_object_or_404(Persona, id=persona_id)

        profile_id = request.session.get("user_profile_id")
        profile = Profile.objects.filter(id=profile_id).first()

        form = ObservacionPersonaForm(request.POST)
        if form.is_valid():
            obs = form.save(commit=False)
            obs.persona = persona
            obs.autor_profile = profile
            obs.rol_autor = "MEDICO"
            obs.save()

        return redirect(f"{request.path}?dni={persona.profile.dni}")