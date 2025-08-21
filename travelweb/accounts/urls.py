from django.urls import path
from . import views

urlpatterns = [
    path("ping/", views.ping),
    path("login/", views.login_view),
    path("request-code/", views.request_code_view),
    path("verify/", views.verify_view),
    path("upload-avatar/", views.upload_avatar_view),
    path("me/", views.me_view),
]
