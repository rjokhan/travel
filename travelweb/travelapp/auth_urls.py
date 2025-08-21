from django.urls import path
from . import auth_views

urlpatterns = [
    path("request-code/", auth_views.request_code, name="auth_request_code"),
    path("verify/", auth_views.verify_code, name="auth_verify_code"),
    path("login/", auth_views.login_view, name="auth_login"),
    path("logout/", auth_views.logout_view, name="auth_logout"),
    path("upload-avatar/", auth_views.upload_avatar, name="auth_upload_avatar"),
    path("me/", auth_views.me, name="auth_me"),
]
