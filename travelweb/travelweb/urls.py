# travelweb/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # публичные страницы/туры
    path("", include("travelapp.urls", namespace="travelapp")),

    # всё, что связано с авторизацией/профилем (me, email login, telegram callback, тестовые)
    path("", include("accounts.urls")),
]

# статика и медиа в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
