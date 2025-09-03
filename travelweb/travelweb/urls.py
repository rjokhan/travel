# travelweb/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def healthcheck(_request):
    return JsonResponse({"ok": True, "app": "travelweb"})

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🛂 Аутентификация (me / upload-avatar / telegram-login / и т.п.)
    path("auth/", include("travelapp.auth_urls")),

    # 🌐 Основной сайт (index, trips и др.)
    # если у вашего приложения есть namespaced urls с app_name='travelapp':
    path("", include(("travelapp.urls", "travelapp"), namespace="travelapp")),

    # простая проверка доступности
    path("health/", healthcheck, name="healthcheck"),
]

# 📦 Статика/медиа для DEV
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
