# travelweb/urls.py
from django.contrib import admin
from django.urls import path
from accounts import views as acc

urlpatterns = [
    path("admin/", admin.site.urls),

    path("auth/request-code/", acc.request_code, name="request_code"),
    path("auth/verify/", acc.verify_code, name="verify_code"),
    path("auth/login/", acc.login_view, name="login"),
    path("auth/me/", acc.me, name="me"),
    path("auth/upload-avatar/", acc.upload_avatar, name="upload_avatar"),
]
