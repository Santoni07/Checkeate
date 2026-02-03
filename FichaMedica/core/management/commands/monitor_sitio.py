import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = "Verifica si el sitio web está en línea y envía alerta por WhatsApp si hay error."

    def handle(self, *args, **kwargs):
        url = "https://www.checkeate.com.ar"
        telefono = "5493516807765"  # tu número sin +
        api_key = "3417172"  # tu API key CallMeBot

        try:
            response = requests.get(url, timeout=10)

            if response.status_code >= 400:
                self.enviar_alerta(
                    f"⚠️ *ALERTA CHECKEATE*\n🚨 Error {response.status_code} en {url}\n🕓 {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')}"
                )
            else:
                print("✅ Sitio en línea correctamente.")

        except requests.exceptions.RequestException as e:
            self.enviar_alerta(
                f"❌ *ALERTA CHECKEATE*\n🌐 El sitio no responde ({type(e).__name__})\n🕓 {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')}"
            )

    def enviar_alerta(self, mensaje):
        try:
            url_api = f"https://api.callmebot.com/whatsapp.php?phone=5493516807765&text={requests.utils.quote(mensaje)}&apikey=3417172"
            response = requests.get(url_api)
            if response.status_code == 200:
                print("📲 Alerta enviada correctamente por WhatsApp.")
            else:
                print(f"⚠️ Error al enviar alerta: {response.status_code}")
        except Exception as e:
            print(f"❌ No se pudo enviar alerta: {e}")