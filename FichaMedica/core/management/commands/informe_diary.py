import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from aptos_generales.models import AptoGeneral
from Cus.models import Cus
from RegistroMedico.models import RegistroMedico

class Command(BaseCommand):
    help = "Envía un informe diario de Checkeate por WhatsApp (usando CallMeBot)."

    def handle(self, *args, **kwargs):
        # Fecha del día anterior
        hoy = timezone.localtime().date()
        ayer = hoy - timedelta(days=1)

        # Contadores
        aptos = AptoGeneral.objects.filter(fecha_creacion__date=ayer).count()
        cus = Cus.objects.filter(fecha_creacion__date=ayer).count()
        registros = RegistroMedico.objects.filter(fecha_creacion__date=ayer).count()
        total = aptos + cus + registros

        # Mensaje con emojis 💬
        mensaje = (
            f"📊 *Informe Diario Checkeate ({ayer.strftime('%d/%m/%Y')})*\n\n"
            f"🏃 Aptos Físicos Generales: {aptos}\n"
            f"🎒 CUS (Certificados Únicos de Salud): {cus}\n"
            f"🩺 Registros Médicos: {registros}\n"
            f"✅ *Total del día:* {total}"
        )

        # Envío por WhatsApp (CallMeBot)
        telefono = "5493516807765"  # tu número (sin +)
        api_key = "3417172"         # tu API key CallMeBot

        try:
            # CallMeBot requiere que el texto esté codificado en URL
            url = f"https://api.callmebot.com/whatsapp.php?phone={telefono}&text={requests.utils.quote(mensaje)}&apikey={api_key}"
            response = requests.get(url)

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✅ Informe diario enviado correctamente por WhatsApp"))
            else:
                self.stdout.write(self.style.ERROR(f"⚠️ Error al enviar WhatsApp: {response.status_code} - {response.text}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Excepción al enviar WhatsApp: {e}"))