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


# ---------- helpers ----------

def ok(**kwargs):
    """Единый успешный ответ."""
    base = {"successful": True, "message": "ok"}
    base.update(kwargs)
    return JsonResponse(base)


def err(msg, code=400):
    """Единый ошибочный ответ (без 500 из view)."""
    return JsonResponse({"successful": False, "message": msg}, status=code)


def _get_profile(user, create=False):
    """
    Безопасно получить профиль пользователя.
    Если related_name у OneToOneField нестандартный, попробуем напрямую через ORM.
    """
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


# ---------- endpoints ----------

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

    # Если пользователь уже существует — не выдаём код регистрации
    if User.objects.filter(username=email).exists():
        return err("Пользователь с таким e-mail уже существует", 409)

    try:
        with transaction.atomic():
            # На всякий случай удалим старые неиспользованные коды
            EmailCode.objects.filter(email=email, purpose="signup", used=False).delete()

            code = generate_code()
            EmailCode.create_signup(
                email=email,
                code=code,
                name=name,
                password_hash=make_password(password),
            )

        # Отправка письма не должна валить сервер ни при каких обстоятельствах
        try:
            send_signup_code(email, code)  # внутренняя реализация уже ловит ошибки
        except Exception:  # паранойя
            log.exception("send_signup_code failed for %s", email)

        return ok()

    except Exception:
        log.exception("request_code failed for %s", email)
        return err("Не удалось выдать код. Попробуйте позже или свяжитесь с поддержкой.", 500)


@require_POST
def verify_code(request):
    """
    POST: email, code
    Проверяем код; создаём пользователя и логиним.
    """
    email = (request.POST.get("email") or "").strip().lower()
    code = (request.POST.get("code") or "").strip()

    if not (email and code):
        return err("Укажите e-mail и код")

    try:
        item = (
            EmailCode.objects.filter(email=email, purpose="signup", used=False)
            .order_by("-created_at")
            .first()
        )
        if not item:
            return err("Код не найден. Запросите новый.")
        # проверка соответствия и срока
        if getattr(item, "code", None) != code:
            return err("Неверный код")
        if hasattr(item, "is_valid") and not item.is_valid():
            return err("Код истёк. Запросите новый.")

        with transaction.atomic():
            # Создание пользователя (idempotent)
            user, created = User.objects.get_or_create(
                username=email, defaults={"email": email}
            )
            if created:
                user.first_name = (item.extra or {}).get("name", "")
                # Пароль положили хэшем в extra.password_hash при создании EmailCode
                user.password = (item.extra or {}).get("password_hash", make_password(None))
                user.save()

            # Профиль существует — ок; нет — создадим
            _get_profile(user, create=True)

            # Помечаем код использованным
            item.used = True
            item.save(update_fields=["used"])

        login(request, user)
        return ok(need_avatar=_need_avatar(user))

    except Exception:
        log.exception("verify_code failed for %s", email)
        return err("Не удалось подтвердить код. Попробуйте ещё раз.", 500)


@require_POST
def login_view(request):
    """
    POST: email, password
    Классический логин.
    """
    email = (request.POST.get("email") or "").strip().lower()
    password = request.POST.get("password") or ""

    if not (email and password):
        return err("Укажите e-mail и пароль")

    try:
        user = authenticate(request, username=email, password=password)
        if not user:
            return err("Неверная пара логин/пароль", 401)

        login(request, user)
        return ok(need_avatar=_need_avatar(user))
    except Exception:
        log.exception("login_view failed for %s", email)
        return err("Ошибка входа. Попробуйте ещё раз.", 500)


def me(request):
    """
    Текущий пользователь.
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({"authenticated": False})

        user = request.user
        prof = _get_profile(user, create=False)
        avatar_url = ""
        if prof and getattr(prof, "avatar", None):
            try:
                avatar_url = prof.avatar.url
            except Exception:
                avatar_url = ""

        return JsonResponse(
            {
                "authenticated": True,
                "email": user.email or user.username,
                "name": user.first_name,
                "avatar_url": avatar_url,
            }
        )
    except Exception:
        log.exception("me endpoint failed")
        return JsonResponse({"authenticated": False})


@require_POST
def upload_avatar(request):
    """
    POST: avatar (file)
    Загрузка/обновление аватара.
    """
    if not request.user.is_authenticated:
        return err("Требуется вход", 401)

    file = request.FILES.get("avatar")
    if not file:
        return err("Файл не передан")

    try:
        prof = _get_profile(request.user, create=True)
        prof.avatar.save(file.name, file, save=True)
        return ok()
    except Exception:
        log.exception("upload_avatar failed for user %s", request.user.pk)
        return err("Не удалось сохранить файл. Попробуйте позже.", 500)
