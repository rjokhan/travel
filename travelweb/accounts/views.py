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

# ---------- endpoints ----------

@require_POST
def request_code(request):
    """
    POST: name, email, password
    Присылаем код на почту. Любые сбои -> контролируемый JSON, не HTML-500.
    """
    try:
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not (name and email and password):
            return err("Заполните все поля")

        if User.objects.filter(username=email).exists():
            return err("Пользователь с таким e-mail уже существует", 409)

        code = generate_code()

        # Создаём запись напрямую, без модельного create_signup()
        with transaction.atomic():
            EmailCode.objects.filter(email=email, purpose="signup", used=False).delete()
            EmailCode.objects.create(
                email=email,
                code=code,
                purpose="signup",
                used=False,
                extra={"name": name, "password_hash": make_password(password)},
            )

        # Отправка письма не должна валить запрос
        try:
            send_signup_code(email, code)
        except Exception:
            log.exception("send_signup_code failed for %s", email)

        return ok()

    except Exception:
        log.exception("request_code failed")
        # ВАЖНО: отдаём JSON, чтобы фронт смог показать message
        return err("Не удалось выдать код. Попробуйте позже или свяжитесь с поддержкой.", 500)


@require_POST
def verify_code(request):
    """POST: email, code — подтверждение, создание пользователя, логин."""
    try:
        email = (request.POST.get("email") or "").strip().lower()
        code = (request.POST.get("code") or "").strip()
        if not (email and code):
            return err("Укажите e-mail и код")

        item = (
            EmailCode.objects.filter(email=email, purpose="signup", used=False)
            .order_by("-created_at")
            .first()
        )
        if not item:
            return err("Код не найден. Запросите новый.")
        if getattr(item, "code", None) != code:
            return err("Неверный код")
        if hasattr(item, "is_valid") and not item.is_valid():
            return err("Код истёк. Запросите новый.")

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=email, defaults={"email": email}
            )
            if created:
                extra = item.extra or {}
                user.first_name = extra.get("name", "")
                user.password = extra.get("password_hash", make_password(None))
                user.save()

            _get_profile(user, create=True)
            item.used = True
            item.save(update_fields=["used"])

        login(request, user)
        return ok(need_avatar=_need_avatar(user))

    except Exception:
        log.exception("verify_code failed")
        return err("Не удалось подтвердить код. Попробуйте ещё раз.", 500)


@require_POST
def login_view(request):
    """POST: email, password — классический вход."""
    try:
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        if not (email and password):
            return err("Укажите e-mail и пароль")

        user = authenticate(request, username=email, password=password)
        if not user:
            return err("Неверная пара логин/пароль", 401)

        login(request, user)
        return ok(need_avatar=_need_avatar(user))
    except Exception:
        log.exception("login_view failed")
        return err("Ошибка входа. Попробуйте ещё раз.", 500)


def me(request):
    """Текущий пользователь (всегда JSON, даже при сбое)."""
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
        return JsonResponse({
            "authenticated": True,
            "email": user.email or user.username,
            "name": user.first_name,
            "avatar_url": avatar_url,
        })
    except Exception:
        log.exception("me endpoint failed")
        return JsonResponse({"authenticated": False})


@require_POST
def upload_avatar(request):
    """POST: avatar — загрузка аватара (контролируемые ошибки)."""
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
        log.exception("upload_avatar failed")
        return err("Не удалось сохранить файл. Попробуйте позже.", 500)
