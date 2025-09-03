# accounts/urls.py (или другой app, где у вас auth-views)
from django.urls import path
from .views import me, test_login, test_logout, telegram_callback

urlpatterns = [
    # проверка авторизации
    path("me/", me, name="me"),

    # тестовые эндпоинты для проверки сессии
    path("auth/test-login/", test_login, name="test_login"),
    path("auth/test-logout/", test_logout, name="test_logout"),

    # колбэк от Telegram Login Widget
    path("auth/telegram/callback/", telegram_callback, name="telegram_callback"),
]
