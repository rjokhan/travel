from django.urls import path
from .views import me, test_login, test_logout

urlpatterns = [
    path("me/", me, name="me"),
    path("auth/test-login/", test_login, name="test_login"),
    path("auth/test-logout/", test_logout, name="test_logout"),
]
