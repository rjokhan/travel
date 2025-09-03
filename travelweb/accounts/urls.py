# travelweb/urls.py  (или accounts/urls.py, если вы его подключаете как главный)
from django.urls import path
from travelapp.auth_views import (
    me,
    login_view,
    logout_view,
    request_code,
    verify_code,
    upload_avatar,
    telegram_callback,
    test_login,
    test_logout,
)

urlpatterns = [
    # Текущий пользователь
    path("me/", me, name="me"),

    # E-mail регистрация и вход
    path("auth/request-code/", request_code, name="request_code"),
    path("auth/verify-code/", verify_code, name="verify_code"),
    path("auth/login/", login_view, name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/upload-avatar/", upload_avatar, name="upload_avatar"),

    # Telegram Login (GET callback)
    path("auth/telegram/callback/", telegram_callback, name="telegram_callback"),

    # Тестовые эндпоинты для диагностики сессий
    path("auth/test-login/", test_login, name="test_login"),
    path("auth/test-logout/", test_logout, name="test_logout"),
]
