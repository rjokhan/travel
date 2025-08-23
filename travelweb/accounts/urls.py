# travelweb/accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("telegram/callback/", views.telegram_callback, name="tg_cb"),
    # ваши существующие /auth/... если оставляете
]
