from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmailSignupCode(models.Model):
    email = models.EmailField(db_index=True)
    name = models.CharField(max_length=150, blank=True)
    # ВНИМАНИЕ: для простоты храним пароль временно в открытом виде и
    # удаляем запись после верификации. В проде лучше шифровать.
    raw_password = models.CharField(max_length=256)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["email", "created_at"])]

    def is_expired(self, minutes=15):
        return self.created_at < timezone.now() - timedelta(minutes=minutes)

    def __str__(self):
        return f"{self.email} [{self.code}] {self.created_at:%Y-%m-%d %H:%M}"
