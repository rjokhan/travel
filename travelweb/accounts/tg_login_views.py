# accounts/tg_login_views.py
import secrets, time
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, login
from django.conf import settings

User = get_user_model()

# простое in-memory хранилище (на проде лучше модель)
_PENDING = {}  # rid -> {"created": ts, "status": "pending|success|failed", "user_id": int|None}
TTL_SEC = 600  # 10 минут

def _gc():
    now = time.time()
    for rid, v in list(_PENDING.items()):
        if now - v["created"] > TTL_SEC:
            _PENDING.pop(rid, None)

@require_POST
@csrf_exempt
def create_request(request: HttpRequest):
    """Создать запрос логина и вернуть rid + deeplink для бота."""
    _gc()
    rid = secrets.token_urlsafe(16)
    _PENDING[rid] = {"created": time.time(), "status": "pending", "user_id": None}
    botname = settings.TELEGRAM_BOT_NAME
    deeplink = f"https://t.me/{botname}?start=login_{rid}"
    return JsonResponse({"successful": True, "rid": rid, "deeplink": deeplink})

def check_status(request: HttpRequest):
    """Проверка статуса логина. На success — логиним пользователя в сессию."""
    _gc()
    rid = request.GET.get("rid", "")
    data = _PENDING.get(rid)
    if not data:
        return JsonResponse({"successful": False, "status": "expired"})
    if data["status"] != "success":
        return JsonResponse({"successful": True, "status": data["status"]})
    user = User.objects.filter(id=data["user_id"]).first()
    if not user:
        return JsonResponse({"successful": False, "status": "failed"})
    login(request, user)
    return JsonResponse({
        "successful": True,
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
        }
    })

@csrf_exempt
def bot_confirm(request: HttpRequest):
    """
    Этот эндпоинт вызывает ваш Telegram-бот после /start login_<rid>.
    Ожидает: rid, tg_id, username, first_name, last_name
    """
    rid = request.GET.get("rid", "")
    tg_id = request.GET.get("tg_id") or ""
    username = (request.GET.get("username") or "").strip().lstrip("@")
    first_name = request.GET.get("first_name") or ""
    last_name = request.GET.get("last_name") or ""

    data = _PENDING.get(rid)
    if not data:
        return JsonResponse({"successful": False, "message": "rid expired"}, status=400)

    # ищем/создаём пользователя
    user = User.objects.filter(username=username).first() if username else None
    if not user:
        base = username or f"tg{tg_id}" or "tguser"
        uname, i = base, 1
        while User.objects.filter(username=uname).exists():
            i += 1
            uname = f"{base}{i}"
        user = User.objects.create_user(
            username=uname,
            first_name=first_name, last_name=last_name,
            password=User.objects.make_random_password(),
        )

    data["status"] = "success"
    data["user_id"] = user.id
    return JsonResponse({"successful": True})
