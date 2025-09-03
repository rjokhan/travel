# travelapp/auth_urls.py
from django.urls import path
from . import auth_views, tg_auth_views   # 👈 tg_auth_views добавим новым файлом

urlpatterns = [
    # старые (по коду/почте)
    path("request-code/", auth_views.request_code, name="auth_request_code"),
    path("verify/", auth_views.verify_code, name="auth_verify_code"),

    # логин/логаут через форму
    path("login/", auth_views.login_view, name="auth_login"),
    path("logout/", auth_views.logout_view, name="auth_logout"),

    # профиль
    path("upload-avatar/", auth_views.upload_avatar, name="auth_upload_avatar"),
    path("me/", auth_views.me, name="auth_me"),

    # 🔹 Telegram WebApp login/signup
    path("telegram-login/", tg_auth_views.telegram_login, name="auth_telegram_login"),
]
