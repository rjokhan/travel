# accounts/tg_login_views.py
import secrets
import time

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

User = get_user_model()

# простое in-memory хранилище (на проде лучше модель/Redis)
_PENDING: dict[str, dict] = {}  # rid -> {"created": ts, "status": "pending|success|failed", "user_id": int|None}
TTL_SEC = 600  # 10 минут

def _gc():
    now = time.time()
    for rid, v in list(_PENDING.items()):
        if now - v.get("created", 0) > TTL_SEC:
            _PENDING.pop(rid, None)

def _ok(data=None, **kw):
    payload = {"successful": True}
    if data:
        payload.update(data)
    payload.update(kw)
    return JsonResponse(payload)

def _err(message, code=400, **extra):
    payload = {"successful": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=code)

@csrf_exempt
@require_POST
def create_request(request: HttpRequest):
    """Создать запрос логина и вернуть rid + deeplink для бота."""
    _gc()
    rid = secrets.token_urlsafe(16)
    _PENDING[rid] = {"created": time.time(), "status": "pending", "user_id": None}

    botname = settings.TELEGRAM_BOT_NAME.lstrip("@")
    deeplink = f"https://t.me/{botname}?start=login_{rid}"
    return _ok(rid=rid, deeplink=deeplink)

@require_GET
def check_status(request: HttpRequest):
    """Проверка статуса логина. На success — логиним пользователя в сессию."""
    _gc()
    rid = request.GET.get("rid", "")
    data = _PENDING.get(rid)
    if not data:
        return _err("expired", code=410, status="expired")

    if data["status"] != "success":
        return _ok(status=data["status"])

    user = User.objects.filter(id=data["user_id"]).first()
    if not user:
        return _err("user not found", status="failed")

    login(request, user)
    return _ok(
        status="success",
        user={
            "id": user.id,
            "username": user.username,
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
        },
    )

@csrf_exempt
@require_POST
def bot_confirm(request: HttpRequest):
    """
    Это вызывает ваш Telegram-бот после /start login_<rid>.
    Ожидает (FORM/QUERY/JSON не важно — берём из request.POST|GET):
      - rid, tg_id, username, first_name, last_name
      - secret — shared key для защиты
    """
    # простая защита: секрет в .env  TELEGRAM_LOGIN_SECRET=xxx
    expected = getattr(settings, "TELEGRAM_LOGIN_SECRET", None)
    got = request.POST.get("secret") or request.GET.get("secret")
    if expected and got != expected:
        return _err("forbidden", code=403)

    # читаем поля
    rid = request.POST.get("rid") or request.GET.get("rid") or ""
    tg_id = (request.POST.get("tg_id") or request.GET.get("tg_id") or "").strip()
    username = (request.POST.get("username") or request.GET.get("username") or "").strip().lstrip("@")
    first_name = (request.POST.get("first_name") or request.GET.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or request.GET.get("last_name") or "").strip()

    data = _PENDING.get(rid)
    if not data:
        return _err("rid expired", code=410)

    # ищем/создаём пользователя
    user = User.objects.filter(username=username).first() if username else None
    if not user:
        base = username or (f"tg_{tg_id}" if tg_id else "tguser")
        uname, i = base, 1
        while User.objects.filter(username=uname).exists():
            i += 1
            uname = f"{base}{i}"
        user = User.objects.create_user(
            username=uname,
            first_name=first_name,
            last_name=last_name,
            password=User.objects.make_random_password(),
        )

    data["status"] = "success"
    data["user_id"] = user.id
    return _ok()
