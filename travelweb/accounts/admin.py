from django.contrib import admin
from .models import EmailSignupCode

@admin.register(EmailSignupCode)
class EmailSignupCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "code", "created_at", "used", "attempts")
    search_fields = ("email", "code")
    list_filter = ("used", "created_at")
