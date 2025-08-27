from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("telegram/callback/", views.telegram_callback, name="telegram_callback"),
    path("me/", views.me, name="me"),                     # ✅ нужно
    path("upload-avatar/", views.upload_avatar, name="upload_avatar"),  # ✅ тоже нужно
]
