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
]
