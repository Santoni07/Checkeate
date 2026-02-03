from django.views import View
from datetime import date
from django.shortcuts import render
from django.db.models import Q

from datetime import datetime, timedelta, date
from django.contrib import messages

from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, DetailView,UpdateView,CreateView,DeleteView,ListView
from .models import RegistroMedico,AntecedenteEnfermedades,EstudiosMedico
from persona.models import JugadorCategoriaEquipo, Jugador
from .forms import AntecedenteEnfermedadesForm,EstudioMedicoForm
from django.contrib.auth.mixins import LoginRequiredMixin
from account.models import Profile


from django.utils.timezone import now
from django.http import JsonResponse


from django.conf import settings
from core.utils.email_utils import enviar_correo




def enviar_notificaciones_diarias(request):
    token = request.GET.get("token")
    if token != settings.SECRET_CRON_TOKEN:
        return JsonResponse({"error": "Acceso no autorizado"}, status=403)

    hoy = now().date()
    total_enviados = 0

    for dias in [15, 5]:
        fecha_objetivo = hoy + timedelta(days=dias)
        print(f"🔎 Buscando fichas con fecha de caducidad = {fecha_objetivo}")

        registros = RegistroMedico.objects.filter(fecha_caducidad=fecha_objetivo)
        print(f"📋 Se encontraron {registros.count()} fichas para {dias} días")

        for ficha in registros:
            jugador = ficha.jugador

            try:
                email_destino = jugador.persona.profile.user.email
                nombre = jugador.persona.profile.nombre
            except Exception as e:
                print(f"⚠️ Error accediendo a email del jugador {jugador.id}: {e}")
                continue

            asunto = f"📅 Tu ficha médica vence en {dias} días - Checkeate"
            cuerpo = (
                f"Hola {nombre},\n\n"
                f"Te recordamos que tu ficha médica vence el día {ficha.fecha_caducidad}.\n"
                "Ingresá a Checkeate para renovarla y evitar problemas.\n\n"
                "🔗 https://www.checkeate.com.ar/login\n\n"
                "— Equipo Checkeate"
            )

            try:
                enviar_correo(asunto, cuerpo, [email_destino], remitente_key="notificaciones")
                print(f"✅ Correo enviado a {email_destino}")
                total_enviados += 1
            except Exception as e:
                print(f"❌ Error al enviar a {email_destino}: {e}")

    return JsonResponse({"status": "ok", "emails_enviados": total_enviados})

class CargarAntecedenteView(FormView):
    template_name = 'registro_medico/cargar_antecedentes.html'
    form_class = AntecedenteEnfermedadesForm
    success_url = reverse_lazy('menu_jugador')

    def _get_registro(self, jugador):
        # 1) si viene por querystring, usarlo (ideal)
        rid = self.request.GET.get('registro_id') or self.kwargs.get('registro_id')
        if rid:
            return get_object_or_404(RegistroMedico, id=rid, jugador=jugador)
        # 2) sin parámetro: último registro del jugador (torneo o competencia)
        return RegistroMedico.objects.filter(jugador=jugador).order_by('-fecha_creacion').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jugador = get_object_or_404(Jugador, id=self.kwargs.get('jugador_id'))
        registro = self._get_registro(jugador)

        context['jugador'] = jugador
        context['ficha_medica'] = registro
        context['es_torneo'] = bool(registro and registro.torneo_id)
        context['es_competencia'] = bool(registro and registro.competencia_id)
        context['evento'] = (registro.torneo if context['es_torneo']
                             else (registro.competencia if context['es_competencia'] else None))
        return context

    def form_valid(self, form):
        jugador = get_object_or_404(Jugador, id=self.kwargs.get('jugador_id'))
        # El antecedente es por jugador, no por ficha
        antecedente, _ = AntecedenteEnfermedades.objects.get_or_create(jugador=jugador)
        for field, value in form.cleaned_data.items():
            setattr(antecedente, field, value)
        antecedente.save()
        return super().form_valid(form)

class VerAntecedenteView(DetailView):
    model = AntecedenteEnfermedades
    template_name = 'registro_medico/ver_antecedentes.html'
    context_object_name = 'antecedente'

    def get_object(self, queryset=None):
        jugador = get_object_or_404(Jugador, id=self.kwargs.get('jugador_id'))
        return get_object_or_404(AntecedenteEnfermedades, jugador=jugador)

    def _get_registro(self, jugador):
        rid = self.request.GET.get('registro_id') or self.kwargs.get('registro_id')
        if rid:
            return get_object_or_404(RegistroMedico, id=rid, jugador=jugador)
        return RegistroMedico.objects.filter(jugador=jugador).order_by('-fecha_creacion').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jugador = self.object.jugador
        registro = self._get_registro(jugador)
        context['ficha_medica'] = registro
        context['profile'] = getattr(self.request.user, 'profile', None)
        context['es_torneo'] = bool(registro and registro.torneo_id)
        context['es_competencia'] = bool(registro and registro.competencia_id)
        context['evento'] = (registro.torneo if context['es_torneo']
                             else (registro.competencia if context['es_competencia'] else None))
        return context

class ModificarAntecedenteView(UpdateView):
    model = AntecedenteEnfermedades
    template_name = 'registro_medico/modificar_antecedentes.html'
    form_class = AntecedenteEnfermedadesForm

    def get_success_url(self):
        return reverse('registroMedico:ver_antecedente',
                       kwargs={'jugador_id': self.object.jugador.id})

    def get_object(self, queryset=None):
        return get_object_or_404(AntecedenteEnfermedades, pk=self.kwargs.get('antecedente_id'))

class ActualizarConsentimientoView(LoginRequiredMixin, UpdateView):
    model = RegistroMedico
    fields = ['consentimiento_persona']
    template_name = 'registro_medico/consentimiento.html'
    success_url = reverse_lazy('menu_jugador')
    login_url = 'login'  # Redirige a login si el usuario no está autenticado

    def form_valid(self, form):
        if not form.instance.consentimiento_persona:
            form.instance.consentimiento_persona = True
            form.instance.save()
            print("Consentimiento actualizado a:", form.instance.consentimiento_persona)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ⚠️ Validación de autenticación antes de consultar el Profile
        user = self.request.user
        if user.is_authenticated:
            profile = Profile.objects.filter(user=user, rol='jugador').first()
            context['profile'] = profile
        else:
            context['profile'] = None  # O redireccioná si querés forzarlo

        ficha_medica = self.get_object()
        context['ficha_medica'] = ficha_medica

        jugador = ficha_medica.jugador
        context['jugador_info'] = jugador

        if jugador:
            categorias = JugadorCategoriaEquipo.objects.filter(jugador=jugador)
            context['categorias_equipo'] = categorias

        print(f"Ficha médica pk: {ficha_medica.pk}")
        return context

# ✅ Cargar un estudio médico asociado a un JUGADOR (no ficha médica)
class CargarEstudioView(LoginRequiredMixin, CreateView):
    model = EstudiosMedico
    form_class = EstudioMedicoForm
    template_name = 'registro_medico/cargar_estudios.html'

    def form_valid(self, form):
        jugador = get_object_or_404(Jugador, id=self.kwargs['jugador_id'])
        print("🔍 Profile ID:", self.request.session.get("user_profile_id"))

        form.instance.jugador = jugador
        print("📦 Registro ID desde el POST:", self.request.POST.get('registro_id'))


        registro_id = self.request.POST.get('registro_id')
        if registro_id:
            form.instance.ficha_medica_id = registro_id
            print("✅ Estudio guardado:", form.instance)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jugador = get_object_or_404(Jugador, id=self.kwargs['jugador_id'])
        context['jugador'] = jugador

        registro_id = self.request.GET.get('registro_id')
        if registro_id:
            registro_medico = RegistroMedico.objects.filter(id=registro_id, jugador=jugador).first()
        else:
            registro_medico = RegistroMedico.objects.filter(jugador=jugador).order_by('-fecha_creacion').first()

        context['registro_medico'] = registro_medico
        return context

    def get_success_url(self):
        profile_id = self.request.session.get("user_profile_id")
        profile = Profile.objects.filter(id=profile_id).first()

        jugador_id = self.kwargs.get('jugador_id')
        registro_id = self.request.POST.get('registro_id')

        if profile:
            if profile.rol == 'jugador':
                return reverse_lazy('registroMedico:ver_estudios', kwargs={'jugador_id': jugador_id})
            elif profile.rol == 'medico' and registro_id:
                return reverse_lazy('registroMedico:registro_medico_update', kwargs={'registro_id': registro_id})

        return reverse_lazy('medico_home')  # Fallback en caso de problemas

# ✅ Listar estudios médicos filtrados por JUGADOR

class EstudiosMedicoListView(ListView):
    model = EstudiosMedico
    template_name = 'registro_medico/estudios_list.html'
    context_object_name = 'estudios'

    def get_queryset(self):
        jugador_id = self.kwargs.get('jugador_id')
        self.jugador_id = jugador_id
        return (
            EstudiosMedico.objects
            .filter(jugador__id=jugador_id)
            .select_related('jugador__persona__profile')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jugador = get_object_or_404(Jugador, id=self.jugador_id)
        context['jugador'] = jugador

        registro = (
            RegistroMedico.objects
            .filter(jugador_id=self.jugador_id)
            .order_by('-fecha_de_llenado')
            .first()
        )
        context['registro_estado'] = registro.estado if registro else 'SIN_REGISTRO'
        context['ficha_medica'] = registro  # <- si querés seguir usando {{ ficha_medica... }} en el template
        return context

# ✅ Eliminar un estudio médico
class EliminarEstudioView(DeleteView):
    model = EstudiosMedico
    template_name = 'registro_medico/eliminar_estudio_confirm.html'
    context_object_name = 'estudio'

    def get_success_url(self):
        jugador_id = self.object.jugador.id  # Obtiene el ID del jugador asociado
        return reverse_lazy('registroMedico:ver_estudios', kwargs={'jugador_id': jugador_id})


class EliminarEstudioMedicoView(DeleteView):
    model = EstudiosMedico
    template_name = 'registro_medico/eliminar_estudio_confirm.html'

    def get_success_url(self):
        registro_id = self.request.GET.get('registro_id')
        if registro_id:
            messages.success(self.request, "✅ Estudio médico eliminado correctamente.")
            return reverse('registro_medico_update_view', kwargs={'registro_id': registro_id})
        else:
            messages.warning(self.request, "⚠️ No se pudo redirigir correctamente.")
            return reverse('medico_home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jugador'] = self.object.jugador
        return context

# ✅ OiHtoria clinica de los registros r

class HistorialAptosView(View):
    template_name = 'registro_medico/historial_aptos.html'

    def get(self, request, jugador_id):
        jugador = get_object_or_404(Jugador, id=jugador_id)

        # 🔵 Solo aptos APROBADOS o VENCIDOS y con fecha_de_llenado válida
        fichas_validas = RegistroMedico.objects.filter(
            jugador=jugador,
            estado__in=['APROBADA', 'VENCIDA'],
            fecha_de_llenado__isnull=False
        ).order_by('-fecha_de_llenado')

        historial = []
        for ficha in fichas_validas:
            if ficha.fecha_de_llenado:
                anio = ficha.fecha_de_llenado.year
                estudios = EstudiosMedico.objects.filter(
                    jugador=jugador,
                    fecha_creacion__year=anio
                )
                historial.append({
                    'ficha': ficha,
                    'estudios': estudios,
                })

        context = {
            'jugador': jugador,
            'historial': historial,
        }
        return render(request, self.template_name, context)