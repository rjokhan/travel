# travelweb/accounts/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from travelapp.models import Profile              # <-- единственный Profile в проекте
from .models import EmailCode                     # <-- только EmailCode из accounts
from .utils import generate_code, send_signup_code


# ---------- helpers ----------

def ok(**kwargs):
    """
    Единый "успешный" ответ.
    """
    base = {"successful": True, "message": "ok"}
    base.update(kwargs)
    return JsonResponse(base)


def err(msg, code=400):
    """
    Единый "ошибочный" ответ.
    """
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
    """
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    if not (name and email and password):
        return err("Заполните все поля")

    # Если пользователь уже существует — не выдаём код регистрации
    if User.objects.filter(username=email).exists():
        return err("Пользователь с таким e-mail уже существует", 409)

    code = generate_code()
    EmailCode.create_signup(
        email=email,
        code=code,
        name=name,
        password_hash=make_password(password),
    )
    send_signup_code(email, code)
    return ok()


@require_POST
def verify_code(request):
    """
    POST: email, code
    Проверяем код; создаём пользователя и логиним.
    """
    email = request.POST.get("email", "").strip().lower()
    code = request.POST.get("code", "").strip()

    item = (
        EmailCode.objects.filter(email=email, purpose="signup", used=False)
        .order_by("-created_at")
        .first()
    )
    if not item or item.code != code or not item.is_valid():
        return err("Неверный или просроченный код")

    # Создание пользователя
    user, created = User.objects.get_or_create(
        username=email, defaults={"email": email}
    )
    if created:
        user.first_name = item.extra.get("name", "")
        user.password = item.extra.get("password_hash", make_password(None))
        user.save()

    # Профиль существует — ок; нет — создадим
    _get_profile(user, create=True)

    # Помечаем код использованным
    item.used = True
    item.save(update_fields=["used"])

    login(request, user)
    return ok(need_avatar=_need_avatar(user))


@require_POST
def login_view(request):
    """
    POST: email, password
    Классический логин.
    """
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    user = authenticate(request, username=email, password=password)
    if not user:
        return err("Неверная пара логин/пароль", 401)

    login(request, user)
    return ok(need_avatar=_need_avatar(user))


def me(request):
    """
    Текущий пользователь.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})

    user = request.user
    prof = _get_profile(user, create=False)
    avatar_url = prof.avatar.url if (prof and getattr(prof, "avatar", None)) else ""

    return JsonResponse(
        {
            "authenticated": True,
            "email": user.email or user.username,
            "name": user.first_name,
            "avatar_url": avatar_url,
        }
    )


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

    prof = _get_profile(request.user, create=True)
    prof.avatar.save(file.name, file, save=True)
    return ok()
