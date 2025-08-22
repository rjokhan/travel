from django.contrib import admin
from .models import EmailCode, Profile

@admin.register(EmailCode)
class EmailCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "code", "used", "expires_at", "created_at")
    list_filter = ("purpose", "used")
    search_fields = ("email", "code")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar")
