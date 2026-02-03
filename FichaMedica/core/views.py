from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from publicidad.models import Publicidad
from core.utils.email_utils import enviar_correo
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from persona.models import ActividadGeneral
from Representate.models import Representante

def error_404(request, exception):
    return render(request, "errors/404.html", status=404)

def error_500(request):
    return render(request, "errors/500.html", status=500)

def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)




@require_GET
def torneos_adheridos(request):
    torneos = (
        Representante.objects
        .select_related("torneo")
        .values_list("torneo__nombre", flat=True)
        .distinct()
    )
    return JsonResponse({
        "tipo": "torneos",
        "items": list(torneos)
    })


@require_GET
def actividades_generales_adheridas(request):


    actividades = (
        ActividadGeneral.objects
        .filter(activo=True)  # opcional, recomendado
        .values_list("nombre", flat=True)
        .order_by("nombre")
    )

    return JsonResponse({
        "tipo": "aptos_generales",
        "items": list(actividades)
    })



def info_prest(request):
    return render(request,'core/info_prest.html')


from django.http import HttpResponse


def test_envio_correo(request):
    try:
        enviar_correo(
            asunto="📅 Test desde vista - Notificaciones",
            cuerpo="Este es un correo de prueba desde notificaciones@checkeate.com.ar",
            destinatarios=["asantoni888@hotmail.com"],
            remitente_key="notificaciones"
        )
        return HttpResponse("✅ Correo enviado con éxito desde la vista.")
    except Exception as e:
        return HttpResponse(f"❌ Error al enviar correo: {str(e)}")






def home(request):
    publicidades = Publicidad.objects.all()

    if request.method == 'POST':
        tipo = request.POST.get("tipo_formulario")

        # ------------------------------
        # FORMULARIO "Quiero ser Prestador"
        # ------------------------------
        if tipo == "quiero_prestador":
            nombre = request.POST.get("name")
            email = request.POST.get("email")
            mensaje = request.POST.get("message")

            cuerpo = f"""
            Consulta desde formulario "Quiero ser prestador":
            Nombre: {nombre}
            Email: {email}
            Mensaje:
            {mensaje}
            """

           # ✅ Respuesta automática al usuario
            cuerpo_usuario = f"""
                Hola {nombre},

                Gracias por comunicarte con Checkeate. Hemos recibido tu consulta y a continuación te dejamos el instructivo para registrarte como **Prestador Médico** 🩺:

                ✨ **Pasos para registrarte:**

                ➡️ Ingresá a nuestra página: https://checkeate.com.ar

                ➡️ Dirigite a la pestaña **"Quiero ser Prestador"**.

                ➡️ Al final de la página hacé clic en **"¿Quieres ser prestador? Haz click aquí"**.

                📧 Ingresá tu email y verificá la validez del mismo.

                📝 Una vez verificado, completá los datos requeridos para finalizar el registro.

                🔑 Cuando termines el registro, iniciá sesión en la plataforma.

                📂 Completá la documentación obligatoria:
                   • Certificado de matrícula (PDF con QR)
                   • Imagen de tu firma con sello médico
                   • Número de matrícula, dirección y teléfono
                   • Aceptar el contrato de prestación de servicios

                ✅ Una vez completada y validada tu documentación, podrás comenzar a realizar los **Aptos Físicos** desde tu cuenta.

                ---

                💙 ¡Gracias por sumarte a nuestra red de profesionales!
                El equipo de **Checkeate**
                """


            enviar_correo(
                asunto='Gracias por contactarnos',
                cuerpo=cuerpo_usuario,
                destinatarios=[email],
                remitente_key='info'
            )
            messages.success(request, '✅ Consulta enviada correctamente.')
            return HttpResponseRedirect(reverse('home') + '#quiero-ser-prestador')

        # ------------------------------
        # FORMULARIO DEL FOOTER
        # ------------------------------
        elif tipo == "footer_contacto":
            nombre = request.POST.get("nombre")
            email = request.POST.get("email")
            mensaje = request.POST.get("mensaje")

            # ✅ Enviar al equipo
            cuerpo_equipo = f"""
            Mensaje desde formulario de pie de página:
            Nombre: {nombre}
            Email: {email}
            Mensaje:
            {mensaje}
            """

            enviar_correo(
                asunto='Consulta desde el Footer',
                cuerpo=cuerpo_equipo,
                destinatarios=['info@checkeate.com.ar'],
                remitente_key='info'
            )

            # ✅ Respuesta automática al usuario
            cuerpo_usuario = f"""
            Hola {nombre},

            Gracias por comunicarte con Checkeate. Hemos recibido tu consulta y te responderemos a la brevedad.

            ¡Saludos!
            El equipo de Checkeate
            """

            enviar_correo(
                asunto='Gracias por contactarnos',
                cuerpo=cuerpo_usuario,
                destinatarios=[email],
                remitente_key='info'
            )

            messages.success(request, '✅ Tu mensaje fue enviado correctamente. Te contactaremos pronto.')
            return HttpResponseRedirect(reverse('home') + '#footer')

    return render(request, 'core/home.html', {'publicidades': publicidades})




