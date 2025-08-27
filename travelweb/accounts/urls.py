# travelweb/accounts/urls.py
from django.urls import path
from . import views  # у тебя telegram_callback уже в accounts/views.py

app_name = "accounts"

urlpatterns = [
    path("telegram/callback/", views.telegram_callback, name="telegram_callback"),
    path("me/", views.me, name="me"),          
    path("upload-avatar/", views.upload_avatar, name="upload_avatar"),
]
