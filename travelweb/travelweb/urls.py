from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path


urlpatterns = [
    path("admin/", admin.site.urls),               # <- стандартная админка
    path("", include("travelapp.urls")),           # <- твое приложение
    path("auth/", include("travelapp.auth_urls")), # новые эндпоинты
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.urls import path, include
urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("", include("travelapp.urls")),
    path("df261d9c024af55022f04b95a82e5e12.txt", mailjet_probe),
]

def mailjet_probe(_):
    # пустой ответ text/plain
    return HttpResponse("", content_type="text/plain")