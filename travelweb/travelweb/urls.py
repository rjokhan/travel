# travelweb/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def mailjet_probe(_):
    # пустой ответ text/plain
    return HttpResponse("", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("travelapp.urls", "travelapp"), namespace="travelapp")),
    path("auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("auth/", include("accounts.urls", namespace="accounts")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
