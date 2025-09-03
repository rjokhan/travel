from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.http import require_GET

User = get_user_model()

@require_GET
def me(request):
    return JsonResponse({
        "authenticated": request.user.is_authenticated,
        "user": getattr(request.user, "username", None),
        "session_key": request.session.session_key,
        "avatar_url": request.session.get("avatar_url"),
    })

@require_GET
def test_login(request):
    # создаём «фиктивного» юзера и логиним
    u, _ = User.objects.get_or_create(username="debug_user")
    login(request, u)
    request.session["avatar_url"] = "https://example.com/x.png"
    return HttpResponseRedirect("/")

@require_GET
def test_logout(request):
    logout(request)
    return HttpResponseRedirect("/")
