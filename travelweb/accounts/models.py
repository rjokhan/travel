# travelweb/accounts/models.py
from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.utils import timezone


class EmailCode(models.Model):
    """
    Одноразовый код (регистрация / сброс пароля).
    Не хранит пароль в открытом виде — только хэш (в extra).
    """

    PURPOSE_SIGNUP = "signup"
    PURPOSE_RESET = "reset"

    PURPOSES = (
        (PURPOSE_SIGNUP, "Sign up"),
        (PURPOSE_RESET, "Password reset"),
    )

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=16, choices=PURPOSES, default=PURPOSE_SIGNUP)
    # сюда кладём дополнительную информацию: name, password_hash и т.п.
    extra = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    # если не задано — проставим при сохранении
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Email code"
        verbose_name_plural = "Email codes"
        ordering = ("-created_at",)
        indexes = [
            # быстрый поиск по емейлу/назначению/флагу использованности
            models.Index(fields=("email", "purpose", "used")),
            models.Index(fields=("created_at",)),
        ]
        # один и тот же активный код не должен дублироваться
        constraints = [
            models.UniqueConstraint(
                fields=("email", "code", "purpose", "used"),
                name="uniq_active_email_code_per_purpose",
            )
        ]

    # --------- helpers ---------

    def __str__(self) -> str:
        return f"{self.email} {self.purpose} {self.code}"

    def is_valid(self) -> bool:
        """Код ещё не использован и не просрочен."""
        return (not self.used) and timezone.now() <= self.expires_at

    def save(self, *args, **kwargs):
        # если expires_at не задан — ставим +15 минут от текущего момента
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    # classmethods для удобного создания

    @classmethod
    def create_signup(cls, email: str, code: str, name: str, password_hash: str) -> "EmailCode":
        """Создаёт код для регистрации и сохраняет name + password_hash в extra."""
        return cls.objects.create(
            email=email,
            code=code,
            purpose=cls.PURPOSE_SIGNUP,
            extra={"name": name, "password_hash": password_hash},
            expires_at=timezone.now() + timedelta(minutes=15),
        )

    @classmethod
    def create_reset(cls, email: str, code: str) -> "EmailCode":
        """Создаёт код для сброса пароля (если понадобится)."""
        return cls.objects.create(
            email=email,
            code=code,
            purpose=cls.PURPOSE_RESET,
            expires_at=timezone.now() + timedelta(minutes=15),
        )
