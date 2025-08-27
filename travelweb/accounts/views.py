# travelweb/accounts/views.py
import hmac
import hashlib
import time

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.views.decorators.csrf import csrf_exempt  # callback будет GET
from django.views.decorators.http import require_http_methods

from travelapp.models import Profile  # ваш профиль

User = get_user_model()


def _tg_check(auth_querydict):
    """Проверка подписи Telegram Login Widget."""
    data = dict(auth_querydict.items())
    hash_ = data.pop("hash", "")

    # Опциональная защита от повторов (5 минут допуска)
    try:
        auth_date = int(data.get("auth_date", "0"))
        if abs(time.time() - auth_date) > 300:
            return False
    except Exception:
        return False

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    calc_hash = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc_hash, hash_)


def _get_or_create_profile(user):
    try:
        return user.profile
    except Exception:
        return Profile.objects.create(user=user)


@csrf_exempt
def telegram_callback(request):
    """
    Callback от Telegram Login Widget (GET с параметрами).
    На входе приходят: id, first_name, username, photo_url, auth_date, hash...
    Поддерживает ?next=/куда-вернуться (необязательно).
    """
    data = request.GET
    if not _tg_check(data):
        return HttpResponseForbidden("Bad signature")

    tg_id = str(data.get("id") or "")
    first_name = data.get("first_name", "") or ""
    _ = (data.get("username") or "").strip().lstrip("@")  # username телеграма (пока не используем)

    # Простейшая привязка: Django-username = tg_{id}
    base_username = f"tg_{tg_id}" if tg_id else "tguser"

    user, created = User.objects.get_or_create(
        username=base_username,
        defaults={"first_name": first_name},
    )

    # Создадим профиль, если нет
    try:
        _get_or_create_profile(user)
    except Exception:
        pass

    # Логиним
    login(request, user)

    # Редиректим обратно, если был передан next
    redirect_to = request.GET.get("next") or "/"
    return HttpResponseRedirect(redirect_to)


# ===== Доп. эндпоинты для фронта (используются вашим JS) =====

def _profile_avatar_url(user):
    """Аккуратно получить URL аватара, если он есть."""
    try:
        p = user.profile  # OneToOne
        if getattr(p, "avatar", None) and getattr(p.avatar, "url", None):
            return p.avatar.url
    except Exception:
        pass
    return None


@require_http_methods(["GET"])
def me(request):
    """
    Лёгкий эндпоинт состояния сессии для фронта.
    Возвращает authenticated, avatar_url, имя/логин (по желанию).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False, "avatar_url": None})

    return JsonResponse({
        "authenticated": True,
        "avatar_url": _profile_avatar_url(request.user),
        "username": getattr(request.user, "username", ""),
        "first_name": getattr(request.user, "first_name", ""),
        "last_name": getattr(request.user, "last_name", ""),
    })


@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    """
    Принимает multipart с полем 'avatar', сохраняет в Profile.avatar (ImageField).
    Проверяет тип и размер, возвращает JSON со ссылкой на файл.
    """
    f = request.FILES.get("avatar")
    if not f:
        return JsonResponse({"successful": False, "message": "Файл не передан"}, status=400)

    if f.content_type not in ("image/jpeg", "image/png", "image/webp"):
        return JsonResponse({"successful": False, "message": "Допустимы JPG/PNG/WebP"}, status=400)

    if f.size > 5 * 1024 * 1024:
        return JsonResponse({"successful": False, "message": "Файл слишком большой (макс 5MB)"}, status=400)

    # Профиль (создадим при необходимости)
    try:
        profile = request.user.profile
    except Exception:
        profile = Profile.objects.create(user=request.user)

    # Сохраняем файл
    profile.avatar = f
    profile.save()

    return JsonResponse({
        "successful": True,
        "avatar_url": getattr(profile.avatar, "url", None),
    })
