# travelweb/accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # callback от Telegram Login Widget
    path("telegram/callback/", views.telegram_callback, name="telegram_callback"),

    # текущий юзер (для index.html скрипта)
    path("me/", views.me, name="me"),

    # загрузка аватарки
    path("upload-avatar/", views.upload_avatar, name="upload_avatar"),

    path("tg/create/", tg.create_request, name="tg_create"),
    path("tg/status/", tg.check_status, name="tg_status"),
    path("tg/confirm/", tg.bot_confirm, name="tg_confirm"),
]
