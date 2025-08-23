# travelweb/accounts/views.py
import logging
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse

from travelapp.models import Profile
from .models import EmailCode
from .utils import generate_code, send_signup_code

log = logging.getLogger(__name__)

def ok(**kwargs):
    base = {"successful": True, "message": "ok"}
    base.update(kwargs)
    return JsonResponse(base)

def err(msg, code=400):
    return JsonResponse({"successful": False, "message": msg}, status=code)

def _get_profile(user, create=False):
    prof = getattr(user, "profile", None)
    if prof:
        return prof
    try:
        return Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        if create:
            return Profile.objects.create(user=user)
        return None

def _need_avatar(user) -> bool:
    prof = _get_profile(user, create=False)
    return not (prof and getattr(prof, "avatar", None))

@require_POST
def request_code(request):
    """
    POST: name, email, password
    Высылаем код подтверждения регистрации на email.
    Никаких 500: ошибки логируем и отдаём понятное сообщение.
    """
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""

    if not (name and email and password):
        return err("Заполните все поля")

    if User.objects.filter(username=email).exists():
        return err("Пользователь с таким e-mail уже существует", 409)

    try:
        with transaction.atomic():
            # Чистим старые неиспользованные коды, чтобы избежать любых уникальных ограничений
            EmailCode.objects.filter(email=email, purpose="signup", used=False).delete()

            code = generate_code()
            # Создание записи с безопасным default для JSON-поля extra
            item = EmailCode.create_signup(
                email=email,
                code=code,
                name=name,
                password_hash=make_password(password),
            )

        # Отправка письма не должна валить сервер ни при каких обстоятельствах
        try:
            send_signup_code(email, code)  # внутри utils желательно fail_silently=True
        except Exception:
            log.exception("send_signup_code failed for %s", email)

        return ok()

    except Exception as e:
        log.exception("request_code failed for %s", email)
        # Возвращаем контролируемую ошибку вместо 500
        return err("Не удалось выдать код. Попробуйте позже или свяжитесь с поддержкой.", 500)
