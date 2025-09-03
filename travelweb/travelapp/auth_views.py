# -*- coding: utf-8 -*-
"""
travelapp/auth_views.py
JSON-эндпоинты для регистрации/входа с подтверждением e-mail и загрузкой аватарки,
а также Telegram Login (GET-callback) + тестовые эндпоинты для быстрой диагностики сессий.

В DEV для простоты POST-вью помечены csrf_exempt. Для продакшена лучше подключить CSRF.
"""

import random
import re
import mimetypes
import hmac
import hashlib
import time
import logging
from typing import Optional

from django.http import JsonResponse, HttpRequest, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.core.mail import send_mail
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.db.models import Q

from .models import RegistrationRequest, Profile

User = get_user_model()
log = logging.getLogger("auth_views")


# ---------- helpers ----------

def _ok(data: Optional[dict] = None, status: int = 200) -> JsonResponse:
    payload = {"successful": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


def _err(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"successful": False, "message": message}, status=status)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _gen_username_from_email(email: str) -> str:
    """
    Для стандартной Django-модели нужен username.
    Генерируем уникальный username по local-части почты.
    """
    base = re.sub(r"[^a-z0-9._-]+", "", email.split("@", 1)[0].lower())[:30] or "user"
    cand = base
    n = 1
    while User.objects.filter(username__iexact=cand).exists():
        suffix = f"-{n}"
        cand = (base[: (30 - len(suffix))] + suffix)
        n += 1
    return cand


# ---------- Telegram GET callback ----------

def _check_tg_signature(params: dict) -> bool:
    """
    Проверка подписи Telegram Login Widget (GET-callback):
    HMAC_SHA256(data_check_string, secret=sha256(BOT_TOKEN)) == hash
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        log.error("TELEGRAM_BOT_TOKEN is not set in settings.")
        return False

    provided = params.get("hash", "")
    # собираем data_check_string из всех ключей кроме 'hash'
    data_check_string = "\n".join(
        f"{k}={params[k]}" for k in sorted(k for k in params.keys() if k != "hash")
    )
    secret = hashlib.sha256(bot_token.encode("utf-8")).digest()
    digest = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided)


@require_GET
def telegram_callback(request: HttpRequest):
    """
    Callback от Telegram Login Widget (GET).
    Пример URL: /auth/telegram/callback/?id=...&username=...&auth_date=...&hash=...&photo_url=...
    1) Проверяем подпись
    2) Создаём/находим пользователя
    3) login(request, user)
    4) redirect на главную (/) — чтобы браузер поставил sessionid к основному домену
    """
    params = request.GET.dict()
    # Лог для быстрой диагностики (не пишем персональные данные)
    log.warning("TG GET callback keys=%s", list(params.keys()))

    # базовые поля
    if not {"auth_date", "hash"}.issubset(params.keys()):
        return HttpResponseRedirect("/")

    # актуальность по времени (24 часа)
    try:
        auth_date = int(params.get("auth_date", "0"))
    except ValueError:
        return HttpResponseRedirect("/")
    if abs(time.time() - auth_date) > 24 * 60 * 60:
        return HttpResponseRedirect("/")

    # подпись
    if not _check_tg_signature(params):
        log.warning("TG callback: hash mismatch")
        return HttpResponseRedirect("/")

    # создаём/логиним
    tg_id = params.get("id")
    username = params.get("username") or f"user_{tg_id}"
    photo = params.get("photo_url")

    if not tg_id:
        return HttpResponseRedirect("/")

    # username храним в виде tg_<id>, чтобы не конфликтовать с e-mail регистрациями
    user, _ = User.objects.get_or_create(
        username=f"tg_{tg_id}",
        defaults={"first_name": username},
    )
    login(request, user)
    # можно хранить avatar_url в сессии для /me/
    if photo:
        request.session["avatar_url"] = photo

    return HttpResponseRedirect("/")


# ---------- тестовые эндпоинты для диагностики сессий ----------

@require_GET
def test_login(request: HttpRequest):
    """
    Принудительный вход для отладки (обходит Телеграм и e-mail поток).
    """
    u, _ = User.objects.get_or_create(username="debug_user")
    login(request, u)
    request.session["avatar_url"] = "https://example.com/x.png"
    return HttpResponseRedirect("/")


@require_GET
def test_logout(request: HttpRequest):
    logout(request)
    return HttpResponseRedirect("/")


# ---------- E-MAIL регистрация / вход ----------

@require_POST
@csrf_exempt
def request_code(request: HttpRequest) -> JsonResponse:
    """
    Шаг 1 регистрации: получаем name/email/password,
    отправляем 6-значный код на почту, сохраняем RegistrationRequest,
    сырой пароль временно кладём в сессию.
    """
    name = (request.POST.get("name") or "").strip()
    email = _normalize_email(request.POST.get("email"))
    password = request.POST.get("password") or ""

    if not name or not email or not password:
        return _err("Заполните имя, e-mail и пароль.")

    if User.objects.filter(Q(email__iexact=email)).exists():
        return _err("Пользователь с таким e-mail уже зарегистрирован.", status=409)

    # создаём/обновляем черновик + код
    code = f"{random.randint(100000, 999999)}"
    RegistrationRequest.objects.filter(email=email).delete()
    RegistrationRequest.create_with_code(name=name, email=email, code_raw=code)

    # пароль в сессию на 15 минут
    request.session[f"reg_pwd:{email}"] = password
    request.session.set_expiry(60 * 15)

    # письмо
    subject = "Код подтверждения — A CLUB TRAVEL"
    body = f"Ваш код подтверждения: {code}\nКод действует 15 минут."
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [email],
            fail_silently=False,
        )
    except Exception as e:
        log.warning("E-mail send failed: %s", e)

    return _ok({"message": "Код отправлен на почту."})


@require_POST
@csrf_exempt
def verify_code(request: HttpRequest) -> JsonResponse:
    """
    Шаг 2 регистрации: проверяем email+code,
    создаём реального пользователя, логиним, помечаем профиль как верифицированный.
    """
    email = _normalize_email(request.POST.get("email"))
    code = (request.POST.get("code") or "").strip()

    try:
        rr = RegistrationRequest.objects.get(email=email)
    except RegistrationRequest.DoesNotExist:
        return _err("Заявка не найдена или уже подтверждена.", status=404)

    if rr.is_expired():
        rr.delete()
        return _err("Код истёк. Запросите новый.", status=410)

    if rr.code_hash != RegistrationRequest.make_hash(code):
        return _err("Неверный код подтверждения.")

    raw_password = request.session.get(f"reg_pwd:{email}")
    if not raw_password:
        rr.delete()
        return _err("Пароль не найден. Запросите код заново.", status=410)

    # создаём пользователя (обычная Django-модель: нужен username)
    username = _gen_username_from_email(email)
    user = User.objects.create_user(
        username=username,
        email=email,
        password=raw_password,
        first_name=rr.name.strip(),
    )

    # профиль уже создался сигналом post_save — отметим верификацию
    try:
        profile: Profile = user.profile  # type: ignore[attr-defined]
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user, display_name=rr.name.strip())
    profile.is_email_verified = True
    if not profile.display_name:
        profile.display_name = rr.name.strip()
    profile.save()

    # очистка черновика + сессии
    try:
        del request.session[f"reg_pwd:{email}"]
    except KeyError:
        pass
    rr.delete()

    # логиним
    login(request, user)
    return _ok({"message": "Почта подтверждена. Загрузите аватар.", "need_avatar": True})


@require_POST
@csrf_exempt
def upload_avatar(request: HttpRequest) -> JsonResponse:
    """
    Загрузка/смена аватарки.
    """
    if not request.user.is_authenticated:
        return _err("Требуется аутентификация.", status=401)

    file: UploadedFile = request.FILES.get("avatar")  # type: ignore[assignment]
    if not file:
        return _err("Загрузите файл аватарки.")

    # простая валидация размера (<= 5 МБ)
    if file.size > 5 * 1024 * 1024:
        return _err("Файл слишком большой (до 5 МБ).")

    # MIME-валидация
    content_type = getattr(file, "content_type", None) or mimetypes.guess_type(file.name)[0]
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        return _err("Поддерживаются только JPG, PNG или WEBP.")

    profile: Profile = request.user.profile  # type: ignore[attr-defined]
    profile.avatar = file
    profile.save(update_fields=["avatar"])

    # абсолютный URL — надёжнее за прокси/Nginx
    try:
        avatar_abs = request.build_absolute_uri(profile.avatar.url)
    except Exception:
        avatar_abs = profile.avatar.url

    return _ok({"message": "Аватар сохранён.", "avatar_url": avatar_abs})


@require_POST
@csrf_exempt
def login_view(request: HttpRequest) -> JsonResponse:
    """
    Вход по e-mail и паролю.
    Т.к. стандартный бэкенд логинит по username, найдём username по e-mail.
    """
    email = _normalize_email(request.POST.get("email"))
    password = request.POST.get("password") or ""

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return _err("Неверная пара e-mail/пароль.", status=401)

    # проверяем, что почта подтверждена
    try:
        if not user.profile.is_email_verified:  # type: ignore[attr-defined]
            return _err("Подтвердите e-mail перед входом.", status=403)
    except Profile.DoesNotExist:
        return _err("Профиль не найден. Обратитесь в поддержку.", status=500)

    # аутентификация через username
    user_auth = authenticate(request, username=user.username, password=password)
    if user_auth is None:
        return _err("Неверная пара e-mail/пароль.", status=401)

    login(request, user_auth)
    need_avatar = not bool(getattr(user_auth.profile, "avatar", None))  # type: ignore[attr-defined]
    return _ok({"message": "Вход выполнен.", "need_avatar": need_avatar})


@require_POST
@csrf_exempt
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return _ok({"message": "Вы вышли из аккаунта."})


@require_GET
@csrf_exempt
def me(request: HttpRequest) -> JsonResponse:
    """
    Текущий пользователь (для фронтенда, чтобы подставлять имя/аватар).
    """
    if not request.user.is_authenticated:
        return _ok({"authenticated": False})

    u = request.user
    prof: Profile = u.profile  # type: ignore[attr-defined]

    # абсолютный URL
    avatar_abs = None
    if getattr(prof, "avatar", None):
        try:
            avatar_abs = request.build_absolute_uri(prof.avatar.url)
        except Exception:
            avatar_abs = prof.avatar.url

    payload = {
        "authenticated": True,
        "email": u.email,
        "name": prof.display_name or u.first_name or u.username,
        "avatar_url": avatar_abs,
        "is_email_verified": prof.is_email_verified,
    }
    # Для быстрой диагностики можно вернуть ключ сессии в DEBUG
    if getattr(settings, "DEBUG", False):
        payload["session_key"] = request.session.session_key
    return _ok(payload)
