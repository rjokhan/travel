# accounts/views.py
import hmac
import hashlib
import time
import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.http import require_GET

User = get_user_model()
log = logging.getLogger("accounts")


@require_GET
def me(request):
    """Проверка текущей авторизации и аватара."""
    return JsonResponse({
        "authenticated": request.user.is_authenticated,
        "user": getattr(request.user, "username", None),
        "avatar_url": request.session.get("avatar_url"),
        "session_key": request.session.session_key,
    })


@require_GET
def test_login(request):
    """Принудительный вход для отладки (обходит Телеграм)."""
    user, _ = User.objects.get_or_create(username="debug_user")
    login(request, user)
    request.session["avatar_url"] = "https://example.com/x.png"
    return HttpResponseRedirect("/")


@require_GET
def test_logout(request):
    """Принудительный выход для отладки."""
    logout(request)
    return HttpResponseRedirect("/")


def _check_tg_auth(data: dict) -> (bool, str):
    """Проверка подписи Telegram (по алгоритму)."""
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False, "no_hash"

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if h != check_hash:
        return False, "hash_mismatch"

    try:
        auth_date = int(data.get("auth_date", "0"))
    except ValueError:
        return False, "bad_auth_date"

    if abs(time.time() - auth_date) > 24 * 60 * 60:
        return False, "auth_date_expired"

    return True, "ok"


@require_GET
def telegram_callback(request):
    """
    Callback от Telegram Login Widget.
    Проверяем hash, создаём/логиним юзера и редиректим на главную.
    """
    data = request.GET.dict()
    ok, reason = _check_tg_auth(data.copy())
    log.warning("TG callback ok=%s reason=%s keys=%s", ok, reason, list(data.keys()))

    if not ok:
        # можно отдать страницу с ошибкой, но лучше редиректить на /
        return HttpResponseRedirect("/")

    tg_id = data.get("id")
    username = data.get("username") or f"user_{tg_id}"
    avatar = data.get("photo_url")

    user, _ = User.objects.get_or_create(
        username=f"tg_{tg_id}",
        defaults={"first_name": username}
    )

    login(request, user)
    request.session["avatar_url"] = avatar

    return HttpResponseRedirect("/")
