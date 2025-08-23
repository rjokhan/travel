# travelweb/accounts/views.py (добавьте)
import hmac, hashlib, time
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt  # callback будет GET
from travelapp.models import Profile  # ваш профиль

User = get_user_model()

def _tg_check(auth_querydict):
    """Проверка подписи Telegram Login Widget."""
    data = dict(auth_querydict.items())
    hash_ = data.pop("hash", "")
    # Опциональная защита от повторов
    try:
        auth_date = int(data.get("auth_date", "0"))
        if abs(time.time() - auth_date) > 300:  # 5 минут допуска
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
    """
    data = request.GET
    if not _tg_check(data):
        return HttpResponseForbidden("Bad signature")

    tg_id = str(data.get("id"))
    first_name = data.get("first_name", "")
    username = data.get("username") or f"tg{tg_id}"

    # Привязку можно хранить как угодно. Простейший вариант: username = tg_{id}
    user, created = User.objects.get_or_create(
        username=f"tg_{tg_id}",
        defaults={"first_name": first_name}
    )

    # Создадим профиль, если нет
    _get_or_create_profile(user)

    # Логиним и отправляем на главную
    login(request, user)
    return HttpResponseRedirect("/")
