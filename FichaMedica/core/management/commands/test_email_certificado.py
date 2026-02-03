from django.core.management.base import BaseCommand
from django.test import RequestFactory
from aptos_generales.models import AptoGeneral
from core.utils.email_utils import enviar_certificado_aprobado_email

class Command(BaseCommand):
    help = "Prueba el envío de correo cuando un certificado es aprobado"

    def handle(self, *args, **options):
        self.stdout.write("===== 🔍 Iniciando prueba de envío de correo =====")
        apto_id = input("👉 Ingresá el ID del AptoGeneral a probar: ")

        try:
            apto = AptoGeneral.objects.get(id=apto_id)
        except AptoGeneral.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ No se encontró el AptoGeneral con ese ID."))
            return

        # ✅ Crear un Request simulado
        factory = RequestFactory()
        request = factory.get("/", secure=True)
        request.META["HTTP_HOST"] = "www.checkeate.com.ar"

        # ✅ Simular build_absolute_uri manualmente (evita el uso de request.scheme)
        def fake_build_absolute_uri(path=""):
            base = "https://www.checkeate.com.ar"
            return f"{base}{path}"
        request.build_absolute_uri = fake_build_absolute_uri

        try:
            enviar_certificado_aprobado_email(apto, "apto", request)
            self.stdout.write(self.style.SUCCESS("✅ Correo enviado correctamente."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al intentar enviar el correo: {e}"))
