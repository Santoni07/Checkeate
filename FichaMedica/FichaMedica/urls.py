from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('info_prest', views.info_prest, name='info_prest'),
    path("", include("core.urls")),

    # Apps
    path('account/', include('account.urls')),
    path('persona/', include('persona.urls')),
    path('registro-medico/', include('RegistroMedico.urls')),
    path('medico/', include('Medico.urls')),
    path('Representate/', include('Representate.urls')),
    path('InfoNovedades/', include('InfoNovedades.urls')),
    path('estudiante/', include('estudiante.urls')),
    path('cus/', include('Cus.urls')),
    path('aptos_generales/', include(('aptos_generales.urls', 'aptos_generales'), namespace='aptos_generales')),
    path(
        'aptos-externos/',
        include('aptos_externos.urls')
    ),
    #Api_Rest
    path("api/", include("ApiRest.urls")),
]

# Solo en DEBUG: servir archivos estáticos y media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================
# Error handlers (producción)
# ==========================
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
handler403 = 'core.views.error_403'
