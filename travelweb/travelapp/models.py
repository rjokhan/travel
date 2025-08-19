# travelapp/models.py
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Country(models.Model):
    name = models.CharField(
        "Страна",
        max_length=80,
        help_text="Официальное название страны (на русском или английском)",
    )
    iso2 = models.CharField(
        "ISO‑код (2 буквы)",
        max_length=2,
        help_text="Например: UZ, RU, KZ. При сохранении будет приведён к верхнему регистру.",
    )

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
        ordering = ("name",)
        # Уникальность ISO2 без учёта регистра + индекс для быстрых поисков
        constraints = [models.UniqueConstraint(Lower("iso2"), name="uniq_country_iso2_ci")]
        indexes = [models.Index(Lower("iso2"), name="idx_country_iso2_ci")]

    def clean(self):
        """
        Нормализуем и валидируем iso2.
        """
        if self.iso2:
            code = self.iso2.strip()
            if len(code) != 2 or not code.isalpha():
                raise ValidationError({"iso2": "ISO‑код должен состоять из 2 латинских букв."})
            self.iso2 = code.upper()

    def __str__(self) -> str:
        return f"{self.name} ({self.iso2})"

    @property
    def flag_emoji(self) -> str:
        """
        Возвращает флаг-эмодзи на основе ISO2 (например, 'UZ' -> 🇺🇿).
        Хранить картинку в БД не нужно.
        """
        try:
            a, b = (self.iso2 or "").upper()
        except ValueError:
            return "🏳️"
        base = 127397  # REGIONAL INDICATOR SYMBOL LETTER A
        return chr(base + ord(a)) + chr(base + ord(b))


def trip_hero_upload_to(instance: "Trip", filename: str) -> str:
    """
    Путь загрузки обложки: trips/hero/<slug>/<YYYY>/<MM>/<filename>
    """
    slug = instance.slug or "trip"
    y_m = instance.date_start.strftime("%Y/%m") if instance.date_start else "0000/00"
    return f"trips/hero/{slug}/{y_m}/{filename}"


class Trip(models.Model):
    THEME_CHOICES = [
        ("forest", "Лес"),
        ("mountain", "Горы"),
        ("sea", "Море"),
        ("desert", "Пустыня"),
        ("city", "Город"),
    ]

    title_full = models.CharField(
        "Полное название",
        max_length=160,
        help_text="Показывается на карточке и странице тура",
    )
    title_short = models.CharField(
        "Короткое название",
        max_length=80,
        help_text="Для слага и компактных мест",
    )
    slug = models.SlugField(
        "Слаг",
        unique=True,
        blank=True,
        help_text="Автогенерация из короткого названия при сохранении",
    )

    country = models.ForeignKey(
        Country,
        verbose_name="Страна",
        on_delete=models.PROTECT,
        related_name="trips",
    )
    theme = models.CharField(
        "Тема оформления", max_length=16, choices=THEME_CHOICES, default="forest"
    )

    date_start = models.DateField("Дата начала")
    date_end = models.DateField("Дата окончания")

    altitude_m = models.PositiveIntegerField(
        "Высота (м)",
        default=0,
        help_text="Максимальная высота маршрута в метрах",
    )
    cities_count = models.PositiveSmallIntegerField(
        "Городов",
        default=1,
        help_text="Сколько городов посещаем",
    )
    capacity = models.PositiveSmallIntegerField("Мест всего", default=20)
    booked = models.PositiveSmallIntegerField("Забронировано мест", default=0)

    price_usd = models.DecimalField(
        "Цена (USD)",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Итоговая цена за участника",
    )

    hero_image = models.ImageField("Обложка", upload_to=trip_hero_upload_to)

    about_md = models.TextField("О туре (Markdown)", blank=True)
    important_md = models.TextField("Важно знать (Markdown)", blank=True)
    payment_md = models.TextField("Оплата (Markdown)", blank=True)

    is_published = models.BooleanField("Публиковать", default=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Путешествие"
        verbose_name_plural = "Путешествия"
        ordering = ("-date_start", "title_full")
        indexes = [
            models.Index(fields=("slug",), name="idx_trip_slug"),
            models.Index(fields=("country", "date_start"), name="idx_trip_country_date"),
            models.Index(fields=("is_published",), name="idx_trip_published"),
        ]
        constraints = [
            # Конец не раньше начала
            models.CheckConstraint(
                check=models.Q(date_end__gte=models.F("date_start")),
                name="chk_trip_dates_valid",
            ),
            # Бронь не больше вместимости
            models.CheckConstraint(
                check=models.Q(booked__lte=models.F("capacity")),
                name="chk_trip_booked_lte_capacity",
            ),
            # Цена не отрицательная
            models.CheckConstraint(
                check=models.Q(price_usd__gte=0), name="chk_trip_price_nonneg"
            ),
        ]

    # --------- Представления/свойства ----------
    def __str__(self) -> str:
        return self.title_full

    @property
    def seats_left(self) -> int:
        return max(0, int(self.capacity) - int(self.booked))

    @property
    def duration_days(self) -> int:
        if self.date_start and self.date_end:
            return (self.date_end - self.date_start).days + 1
        return 0

    @property
    def date_range_str(self) -> str:
        if self.date_start and self.date_end:
            return f"{self.date_start:%d/%m} – {self.date_end:%d/%m}"
        return ""

    def get_absolute_url(self):
        return reverse("trip_detail", kwargs={"slug": self.slug})

    # --------- Валидация и автогенерация ----------
    def clean(self):
        errors = {}
        # Даты
        if self.date_start and self.date_end and self.date_end < self.date_start:
            errors["date_end"] = "Дата окончания не может быть раньше даты начала."

        # Больше брони, чем мест
        if self.capacity is not None and self.booked is not None and self.booked > self.capacity:
            errors["booked"] = "Забронировано больше, чем доступная вместимость."

        # Цена
        if self.price_usd is not None and self.price_usd < 0:
            errors["price_usd"] = "Цена не может быть отрицательной."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Автогенерация слага (стабильный и короткий)
        if not self.slug:
            base = slugify(self.title_short or self.title_full)[:50] or "trip"
            slug = base
            if type(self).objects.filter(slug=slug).exists():
                slug = f"{base}-{self.date_start:%Y%m%d}" if self.date_start else f"{base}-1"
            self.slug = slug

        # На всякий случай приводим booked в допустимый диапазон
        if self.capacity is not None and self.booked is not None and self.booked > self.capacity:
            self.booked = self.capacity

        super().save(*args, **kwargs)
