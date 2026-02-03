from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.hashers import make_password

from .models import Profile


# =========================
# PROFILE ADMIN
# =========================
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'nombre',
        'apellido',
        'dni',
        'fecha_nacimiento',
        'email',
        'rol',
    )

    search_fields = (
        'user__username',
        'nombre',
        'apellido',
        'email',
    )

    list_filter = ('rol',)
    list_editable = ('rol',)

    def save_model(self, request, obj, form, change):
        # Asegurar contraseña cifrada
        if obj.user and obj.user.password and not obj.user.password.startswith('pbkdf2_'):
            obj.user.password = make_password(obj.user.password)
            obj.user.save()
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


admin.site.register(Profile, ProfileAdmin)


# =========================
# USER ADMIN (PERSONALIZADO)
# =========================
admin.site.unregister(User)  # 🔴 CLAVE

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'date_joined',   # ✅ FECHA CREACIÓN
        'last_login',
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
    )

    ordering = ('-date_joined',)
