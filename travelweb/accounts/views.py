import random
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import EmailSignupCode

User = get_user_model()

def _json_error(msg, status=400):
    return JsonResponse({"successful": False, "message": msg}, status=status)

def ping(request):
    return JsonResponse({"message": "pong"})

@require_POST
def login_view(request):
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if not user:
        return _json_error("Неверный e-mail или пароль")
    login(request, user)
    return JsonResponse({"successful": True, "need_avatar": False})

@require_POST
def request_code_view(request):
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip().lower()
    raw_password = request.POST.get("password") or ""

    if not email or "@" not in email:
        return _json_error("Некорректный e-mail")
    if len(raw_password) < 6:
        return _json_error("Пароль должен быть не короче 6 символов")

    # Уже есть такой пользователь?
    if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
        return _json_error("Пользователь с таким e-mail уже зарегистрирован. Войдите.")

    # Rate limit: не чаще 1 письма в минуту
    last = EmailSignupCode.objects.filter(email=email, used=False).order_by("-created_at").first()
    if last and (timezone.now() - last.created_at).total_seconds() < 60:
        return _json_error("Код уже отправлён. Попробуйте ещё раз через минуту.", status=429)

    code = str(random.randint(100000, 999999))
    rec = EmailSignupCode.objects.create(email=email, name=name, raw_password=raw_password, code=code)

    subject = "Код подтверждения — A CLUB TRAVEL"
    body = f"Ваш код подтверждения: {code}\nОн действителен 15 минут.\nЕсли вы не запрашивали код — игнорируйте письмо."
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    except BadHeaderError:
        return _json_error("Ошибка заголовков письма")
    except Exception as e:
        # если SMTP не настроен — сообщим
        return _json_error(f"Не удалось отправить письмо: {e}")

    return JsonResponse({"successful": True, "message": "Код отправлен"})

@require_POST
def verify_view(request):
    email = (request.POST.get("email") or "").strip().lower()
    code = (request.POST.get("code") or "").strip()

    rec = EmailSignupCode.objects.filter(email=email, used=False).order_by("-created_at").first()
    if not rec:
        return _json_error("Код не найден. Запросите новый.")
    if rec.is_expired(15):
        return _json_error("Срок действия кода истёк. Запросите новый.")
    if rec.attempts >= 5:
        return _json_error("Превышено число попыток. Запросите новый код.", status=429)

    if rec.code != code:
        rec.attempts += 1
        rec.save(update_fields=["attempts"])
        return _json_error("Неверный код")

    # Создаём пользователя (username = email)
    if User.objects.filter(username=email).exists():
        user = User.objects.get(username=email)
    else:
        user = User.objects.create_user(username=email, email=email, password=rec.raw_password)
        if rec.name:
            # сохраним имя
            user.first_name = rec.name
            user.save(update_fields=["first_name"])

    rec.used = True
    rec.save(update_fields=["used"])

    login(request, user)
    return JsonResponse({"successful": True, "need_avatar": True})

@require_POST
@login_required
def upload_avatar_view(request):
    f = request.FILES.get("avatar")
    if not f:
        return _json_error("Файл не передан")
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    path = default_storage.save(f"avatars/{request.user.username}_{f.name}", ContentFile(f.read()))
    return JsonResponse({"successful": True, "avatar_url": settings.MEDIA_URL + path})

def me_view(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "name": (getattr(request.user, "first_name", "") or request.user.username),
            "email": getattr(request.user, "email", ""),
            "avatar_url": None,
        })
    return JsonResponse({"authenticated": False})
