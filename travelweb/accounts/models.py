# travelweb/accounts/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmailCode(models.Model):
    PURPOSES = (("signup", "Sign up"), ("reset", "Password reset"))
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=16, choices=PURPOSES, default="signup")
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    @classmethod
    def create_signup(cls, email, code, name, password_hash):
        return cls.objects.create(
            email=email,
            code=code,
            purpose="signup",
            extra={"name": name, "password_hash": password_hash},
            expires_at=timezone.now() + timedelta(minutes=15),
        )

    def is_valid(self) -> bool:
        return (not self.used) and timezone.now() <= self.expires_at

    def __str__(self):
        return f"{self.email} {self.purpose} {self.code}"
