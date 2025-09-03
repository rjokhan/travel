# travelapp/tg_auth_views.py
"""
Telegram WebApp login (session-based) для Django.

POST /api/auth/telegram-login/
Тело запроса:
  Вариант A (WebApp, рекомендовано):
    - initData = raw-строка из window.Telegram.WebApp.initData
  Вариант B (fallback для Login Widget, не WebApp):
    - id, username?, first_name?, last_name?, auth_date, hash

Проверка подписи:
  HMAC-SHA256(data_check_string, secret_key=sha256(BOT_TOKEN))
  и сверка с полем 'hash'. Истекает через AUTH_MAX_AGE_SECONDS.
"""

import hmac
import json
import time
import hashlib
import urllib.parse
from typing import Dict, Tuple, Any, Optional

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

User = get_user_model()
AUTH_MAX_AGE_SECONDS = 15 * 60  # 15 минут


def _ok(data: Optional[dict] = None, status: int = 200) -> JsonResponse:
    payload = {"successful": True}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


def _err(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"successful": False, "message": message}, status=status)


def _require_bot_token() -> str:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in settings.")
    return token


def _build_data_check_string(params: Dict[str, Any]) -> str:
    """
    Собираем data_check_string по документации Telegram:
    - сортируем ключи (ASCII) кроме 'hash'
    - если 'user' — словарь, сериализуем compact JSON без пробелов
    """
    items = []
    for key in sorted(k for k in params.keys() if k != "hash"):
        val = params[key]
        if key == "user" and isinstance(val, dict):
            val = json.dumps(val, separators=(",", ":"), ensure_ascii=False)
        else:
            val = str(val)
        items.append(f"{key}={val}")
    return "\n".join(items)


def _verify_hash(params: Dict[str, Any], bot_token: str) -> bool:
    """
    Сравнение HMAC-SHA256(data_check_string, secret=sha256(bot_token)) с params['hash'].
    """
    provided_hash = params.get("hash", "")
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    data_check_string = _build_data_check_string(params)
    digest = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided_hash)


def _parse_init_data(init_data_raw: str) -> Dict[str, Any]:
    """
    Парсим Telegram.WebApp.initData (querystring-like):
    'query_id=...&user=%7B...%7D&auth_date=...&hash=...'
    """
    parsed = urllib.parse.parse_qs(init_data_raw, keep_blank_values=True, strict_parsing=False)
    flat: Dict[str, Any] = {}
    for k, v in parsed.items():
        flat[k] = v[0] if v else ""
    # user JSON → dict
    if "user" in flat:
        try:
            flat["user"] = json.loads(flat["user"])
        except Exception:
            pass
    return flat


def _extract_telegram_user(params: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Возвращает (user_dict, error_message). Поддерживает:
    - WebApp initData: params['user'] — dict
    - Login Widget: плоские поля id/username/first_name/last_name
    """
    if isinstance(params.get("user"), dict):
        u = params["user"]
        if "id" not in u:
            return None, "Telegram 'user' has no id."
        return {
            "id": u.get("id"),
            "username": u.get("username"),
            "first_name": u.get("first_name"),
            "last_name": u.get("last_name"),
        }, None

    # fallback — плоские поля
    required = ("id", "auth_date", "hash")
    if all(k in params for k in required):
        return {
            "id": params.get("id"),
            "username": params.get("username"),
            "first_name": params.get("first_name"),
            "last_name": params.get("last_name"),
        }, None

    return None, "No Telegram user data found."


def _ensure_local_user(tg: Dict[str, Any]) -> User:
    """
    Создаём/находим локального юзера. username: @username если есть, иначе 'tg_<id>'.
    """
    tg_id = str(tg["id"])
    base_username = (tg.get("username") or "").strip()
    candidate = base_username if base_username else f"tg_{tg_id}"

    # если занято — добавляем суффикс
    username = candidate
    suffix = 1
    while User.objects.filter(username__iexact=username).exclude(username=candidate).exists():
        suffix += 1
        username = f"{candidate}_{suffix}"

    user = User.objects.filter(username__iexact=candidate).first()
    if not user and candidate != username:
        user = User.objects.filter(username__iexact=username).first()

    if not user:
        user = User.objects.create_user(username=username)
        user.set_unusable_password()

    # Обновим имена, если есть
    first_name = (tg.get("first_name") or "").strip()
    last_name = (tg.get("last_name") or "").strip()
    changed = False
    if first_name and user.first_name != first_name:
        user.first_name = first_name
        changed = True
    if last_name and user.last_name != last_name:
        user.last_name = last_name
        changed = True
    if changed:
        user.save(update_fields=["first_name", "last_name"])

    return user


@csrf_exempt
@require_POST
def telegram_login(request: HttpRequest) -> JsonResponse:
    """
    Проверяем подпись Telegram и логиним пользователя (cookie-сессия Django).
    Принимает:
      - initData (WebApp)
      ИЛИ
      - id/username/first_name/last_name/auth_date/hash (Login Widget)
    """
    try:
        bot_token = _require_bot_token()
    except RuntimeError as e:
        return _err(str(e), status=500)

    init_data_raw = request.POST.get("initData", "").strip()

    # Normalize params
    if init_data_raw:
        params = _parse_init_data(init_data_raw)
    else:
        params = {
            k: (request.POST.get(k) or "").strip()
            for k in ("id", "username", "first_name", "last_name", "auth_date", "hash")
            if k in request.POST
        }

    # Базовые проверки
    if "auth_date" not in params or "hash" not in params:
        return _err("Missing auth_date/hash.", status=400)

    # Срок годности
    try:
        auth_date = int(params["auth_date"])
    except ValueError:
        return _err("Invalid auth_date.", status=400)

    now = int(time.time())
    if now - auth_date > AUTH_MAX_AGE_SECONDS:
        return _err("Auth data is too old. Please re-open via Telegram.", status=401)

    # Проверка подписи
    if not _verify_hash(params, bot_token):
        return _err("Telegram signature check failed.", status=401)

    # Достаём юзера из параметров
    tg_user, err = _extract_telegram_user(params)
    if err:
        return _err(err, status=400)
    if not tg_user or not tg_user.get("id"):
        return _err("Invalid Telegram user.", status=400)

    # Создаём/находим и логиним
    user = _ensure_local_user(tg_user)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    # Вернём avatar_url, если уже есть (загрузить можно отдельным эндпоинтом)
    profile = getattr(user, "profile", None)
    avatar_url = None
    if profile and profile.avatar:
        try:
            avatar_url = request.build_absolute_uri(profile.avatar.url)
        except Exception:
            avatar_url = None

    return _ok({
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": avatar_url,
        },
        "message": "Logged in via Telegram.",
    })
