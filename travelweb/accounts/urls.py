# accounts/urls.py
from django.urls import path
from travelapp.auth_views import (
    me,
    login_view,
    logout_view,
    request_code,
    verify_code,
    upload_avatar,
    telegram_callback,   # GET колбэк Telegram Login Widget
    test_login,
    test_logout,
)

urlpatterns = [
    # состояние сессии
    path("me/", me, name="me"),

    # e-mail регистрация/вход
    path("auth/request-code/", request_code, name="request_code"),
    path("auth/verify-code/", verify_code, name="verify_code"),
    path("auth/login/", login_view, name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/upload-avatar/", upload_avatar, name="upload_avatar"),

    # Telegram GET callback
    path("auth/telegram/callback/", telegram_callback, name="telegram_callback"),

    # диагностика сессий
    path("auth/test-login/", test_login, name="test_login"),
    path("auth/test-logout/", test_logout, name="test_logout"),
]
