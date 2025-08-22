import json
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # не нужно, если есть csrftoken
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import EmailCode, Profile
from .utils import generate_code, send_signup_code


def ok(**kwargs):
    base = {"successful": True, "message": "ok"}
    base.update(kwargs)
    return JsonResponse(base)

def err(msg, code=400):
    return JsonResponse({"successful": False, "message": msg}, status=code)


@require_POST
def request_code(request):
    """
    POST: name, email, password
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
        email=email, code=code, name=name, password_hash=make_password(password)
    )
    send_signup_code(email, code)
    return ok()


@require_POST
def verify_code(request):
    """
    POST: email, code
    Создаём пользователя и логиним.
    """
    email = request.POST.get("email", "").strip().lower()
    code = request.POST.get("code", "").strip()

    try:
        item = (
            EmailCode.objects.filter(email=email, purpose="signup", used=False)
            .order_by("-created_at")
            .first()
        )
        if not item or item.code != code or not item.is_valid():
            return err("Неверный или просроченный код")
    except EmailCode.DoesNotExist:
        return err("Код не найден")

    # Создание пользователя
    user, created = User.objects.get_or_create(username=email, defaults={"email": email})
    if created:
        user.first_name = item.extra.get("name", "")
        user.password = item.extra.get("password_hash", make_password(None))
        user.save()
        Profile.objects.get_or_create(user=user)

    item.used = True
    item.save(update_fields=["used"])

    login(request, user)

    need_avatar = not (hasattr(user, "profile") and user.profile.avatar)
    return ok(need_avatar=need_avatar)


@require_POST
def login_view(request):
    """
    POST: email, password
    """
    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    user = authenticate(request, username=email, password=password)
    if not user:
        return err("Неверная пара логин/пароль", 401)

    login(request, user)
    need_avatar = not (hasattr(user, "profile") and user.profile.avatar)
    return ok(need_avatar=need_avatar)


def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    user = request.user
    avatar_url = ""
    if hasattr(user, "profile") and user.profile.avatar:
        avatar_url = user.profile.avatar.url
    return JsonResponse({
        "authenticated": True,
        "email": user.email or user.username,
        "name": user.first_name,
        "avatar_url": avatar_url,
    })


@require_POST
def upload_avatar(request):
    if not request.user.is_authenticated:
        return err("Требуется вход", 401)
    file = request.FILES.get("avatar")
    if not file:
        return err("Файл не передан")

    prof, _ = Profile.objects.get_or_create(user=request.user)
    prof.avatar.save(file.name, file, save=True)
    return ok()
