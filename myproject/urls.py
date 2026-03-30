# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from main.views import set_language_get

admin.site.site_header = "AUTOLIGA ADMIN"
admin.site.site_title = "AUTOLIGA"
admin.site.index_title = "Р В РЎвЂ™Р В РўвЂР В РЎР В РЎвЂР В Р вЂ¦ Р В РЎвЂ”Р В Р’В°Р В Р вЂ¦Р В Р’ВµР В Р’В»Р РЋР Р‰ Autoliga Site"

# ========== Р В РІР‚Р В РЎвЂ™Р В РІР‚вЂќР В РЎвЂєР В РІР‚в„ўР В Р’В«Р В РІР‚Сћ Р В Р’В Р В РЎвЂєР В Р в‚¬Р В РЎС›Р В Р’В« (Р В Р’В±Р В Р’ВµР В Р’В· Р РЋР РЏР В Р’В·Р РЋРІР‚в„–Р В РЎвЂќР В Р’В°) ==========
urlpatterns = [
    path('admin/', admin.site.urls),
    path('set-language/', set_language_get, name='set_language'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('nested_admin/', include('nested_admin.urls')),
    
    # API endpoints
    path('api/', include('main.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += [
    path('', include('main.urls')), 
]

urlpatterns += i18n_patterns(
    path('', include('main.urls')),
    prefix_default_language=False  
)

urlpatterns += [
    path('captcha/', include('captcha.urls'))
    ]

# ========== Р В РЎС™Р В РІР‚СћР В РІР‚СњР В Р В РЎвЂ™ Р В  Р В Р Р‹Р В РЎС›Р В РЎвЂ™Р В РЎС›Р В Р В РЎв„ўР В РЎвЂ™ (Р РЋРІР‚С™Р В РЎвЂўР В Р’В»Р РЋР Р‰Р В РЎвЂќР В РЎвЂў DEBUG) ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root='')