# travelweb/accounts/admin.py
from django.contrib import admin
from .models import EmailCode

@admin.register(EmailCode)
class EmailCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "code", "used", "expires_at", "created_at")
    list_filter = ("purpose", "used")
    search_fields = ("email", "code")
