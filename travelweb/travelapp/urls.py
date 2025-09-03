# travelweb/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # маршруты приложения с турами
    path("", include("travelapp.urls", namespace="travelapp")),

    # маршруты аккаунтов (в т.ч. Telegram login)
    path("", include("accounts.urls")),  # 👈 здесь подключаем accounts/urls.py
]

# статика и медиа в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
