from django.urls import path
from . import views

urlpatterns = [
    path("request-code/", views.request_code, name="request_code"),
    path("verify/", views.verify_code, name="verify_code"),
    path("login/", views.login_view, name="login_view"),
    path("me/", views.me, name="me"),
    path("upload-avatar/", views.upload_avatar, name="upload_avatar"),
]
