# travelweb/accounts/urls.py
from django.urls import path

from . import views
from . import tg_login_views   # ← обязательно импортируем файл с tg-вьюхами

app_name = "accounts"

urlpatterns = [
    # Telegram Login Widget (прямой коллбек)
    path("telegram/callback/", views.telegram_callback, name="telegram_callback"),

    # вспомогательные эндпоинты для фронта
    path("me/", views.me, name="me"),
    path("upload-avatar/", views.upload_avatar, name="upload_avatar"),

    # 🔐 альтернативный flow через бота (rid → подтверждение в боте)
    path("tg/create/",  tg_login_views.create_request, name="tg_create"),
    path("tg/status/",  tg_login_views.check_status,  name="tg_status"),
    path("tg/confirm/", tg_login_views.bot_confirm,    name="tg_confirm"),
]
