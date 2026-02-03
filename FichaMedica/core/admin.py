from django.contrib import admin
from .models import EmailLog

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("tipo", "destinatario", "asunto", "estado", "fecha_envio")
    list_filter = ("tipo", "estado", "fecha_envio")
    search_fields = ("destinatario", "asunto")
