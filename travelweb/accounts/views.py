from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

def ping(request):
    return JsonResponse({"message": "pong"})

@require_POST
def login_view(request):
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if not user:
        return JsonResponse({"successful": False, "message": "Неверный e‑mail или пароль"}, status=400)
    login(request, user)
    return JsonResponse({"successful": True, "need_avatar": False})

@require_POST
def request_code_view(request):
    return JsonResponse({"successful": True, "message": "Код отправлен"})

@require_POST
def verify_view(request):
    return JsonResponse({"successful": True})

@require_POST
@login_required
def upload_avatar_view(request):
    f = request.FILES.get("avatar")
    if not f:
        return JsonResponse({"successful": False, "message": "Файл не передан"}, status=400)
    filename = f"avatars/{request.user.username or request.user.id}_{f.name}"
    path = default_storage.save(filename, ContentFile(f.read()))
    return JsonResponse({"successful": True, "avatar_url": settings.MEDIA_URL + path})

def me_view(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "authenticated": True,
            "name": getattr(request.user, "first_name", "") or request.user.username,
            "email": getattr(request.user, "email", ""),
            "avatar_url": None,
        })
    return JsonResponse({"authenticated": False})
