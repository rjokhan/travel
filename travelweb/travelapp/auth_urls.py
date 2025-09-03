# travelapp/auth_urls.py
from django.urls import path
from . import auth_views, tg_auth_views

urlpatterns = [
    # E-mail код (если используешь параллельно)
    path("request-code/", auth_views.request_code, name="auth_request_code"),
    path("verify/", auth_views.verify_code, name="auth_verify_code"),

    # Классический логин/логаут
    path("login/", auth_views.login_view, name="auth_login"),
    path("logout/", auth_views.logout_view, name="auth_logout"),

    # Профиль
    path("upload-avatar/", auth_views.upload_avatar, name="auth_upload_avatar"),
    path("me/", auth_views.me, name="auth_me"),

    # Telegram
    path("telegram-login/", tg_auth_views.telegram_login, name="auth_telegram_login"),       # POST (WebApp initData)
    path("telegram-callback/", tg_auth_views.telegram_callback, name="auth_telegram_callback"),  # GET (Login Widget)
]
