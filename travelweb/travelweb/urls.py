from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("grappelli/", include("grappelli.urls")),  # <- подключаем Grappelli
    path("admin/", admin.site.urls),               # <- стандартная админка
    path("", include("travelapp.urls")),           # <- твое приложение
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
