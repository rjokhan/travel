# travelapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from .models import Country, Trip

# --- Снять возможные старые регистрации (чтобы не ловить AlreadyRegistered) ---
from django.contrib.admin.sites import NotRegistered
for mdl in (Country, Trip):
    try:
        admin.site.unregister(mdl)
    except NotRegistered:
        pass


# =========================
# Country
# =========================
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "iso2")
    search_fields = ("name", "iso2")
    ordering = ("name",)


# =========================
# Trip — вспомогалки
# =========================
class TripStatusFilter(admin.SimpleListFilter):
    """Быстрый фильтр по состоянию тура (по датам и публикации)."""
    title = _("Состояние тура")
    parameter_name = "state"

    def lookups(self, request, model_admin):
        return (
            ("active", _("Активные")),
            ("soon", _("Скоро")),
            ("past", _("Завершённые")),
            ("draft", _("Черновики")),
        )

    def queryset(self, request, qs):
        today = timezone.now().date()
        if self.value() == "active":
            return qs.filter(is_published=True, date_start__lte=today, date_end__gte=today)
        if self.value() == "soon":
            return qs.filter(is_published=True, date_start__gt=today)
        if self.value() == "past":
            return qs.filter(date_end__lt=today)
        if self.value() == "draft":
            return qs.filter(is_published=False)
        return qs


def _state_label(obj):
    """('Метка', 'css-класс') по датам/публикации."""
    today = timezone.now().date()
    if not obj.is_published:
        return "Черновик", "warn"
    if obj.date_end and obj.date_end < today:
        return "Завершён", "danger"
    if obj.date_start and obj.date_start > today:
        return "Скоро", "warn"
    return "Активен", "ok"


# =========================
# Trip
# =========================
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    # ----- список -----
    list_display = (
        "thumb",
        "title_full",
        "country",
        "theme_pill",
        "dates",
        "price_fmt",
        "free_badge",
        "state_badge",
    )
    list_display_links = ("thumb", "title_full")
    list_filter = ("country", "theme", "is_published", TripStatusFilter, "date_start")
    search_fields = ("title_full", "title_short", "country__name")
    date_hierarchy = "date_start"
    ordering = ("-date_start", "title_full")
    list_per_page = 25
    actions = ("publish_selected", "unpublish_selected", "duplicate_selected", "export_csv")

    # ----- форма -----
    readonly_fields = ("free_info", "date_range_preview", "created_at", "updated_at")
    fieldsets = (
        (_("Основная информация"), {
            "fields": ("title_full", "title_short", "slug", "country", "theme", "is_published", "hero_image")
        }),
        (_("Даты и места"), {
            "fields": ("date_start", "date_end", "capacity", "booked", "free_info", "date_range_preview",
                       "altitude_m", "cities_count")
        }),
        (_("Цена"), {"fields": ("price_usd",)}),
        (_("Контент (Markdown)"), {"fields": ("about_md", "important_md", "payment_md")}),
        (_("Служебные"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    # ---------- отображение полей ----------
    def thumb(self, obj):
        if obj.hero_image:
            return format_html('<img src="{}" class="ac-thumb" alt="cover"/>', obj.hero_image.url)
        return "—"
    thumb.short_description = " "

    def dates(self, obj):
        if obj.date_start and obj.date_end:
            return f"{obj.date_start:%d.%m.%Y} — {obj.date_end:%d.%m.%Y}"
        return "—"
    dates.short_description = _("Даты")

    def price_fmt(self, obj):
        return f"{obj.price_usd:,.0f} USD".replace(",", " ")
    price_fmt.short_description = _("Цена")

    def free_badge(self, obj):
        free = obj.seats_left
        cls = "ok" if free > 5 else ("warn" if free > 0 else "danger")
        return format_html('<span class="badge-status {}">Свободно: {}</span>', cls, free)
    free_badge.short_description = _("Места")

    def state_badge(self, obj):
        label, cls = _state_label(obj)
        return format_html('<span class="badge-status {}">{}</span>', cls, label)
    state_badge.short_description = _("Статус")

    def theme_pill(self, obj):
        return format_html('<span class="theme-dot {}"></span>{}', obj.theme, obj.get_theme_display())
    theme_pill.short_description = _("Тема")

    def free_info(self, obj):
        return format_html("<b>Свободных мест:</b> {}", obj.seats_left)
    free_info.short_description = _("Свободные места")

    def date_range_preview(self, obj):
        return obj.date_range_str
    date_range_preview.short_description = _("Диапазон дат")

    # ---------- actions ----------
    @admin.action(description=_("Опубликовать выбранные"))
    def publish_selected(self, request, qs):
        updated = qs.update(is_published=True)
        self.message_user(request, f"Опубликовано: {updated}")

    @admin.action(description=_("Снять с публикации"))
    def unpublish_selected(self, request, qs):
        updated = qs.update(is_published=False)
        self.message_user(request, f"Снято с публикации: {updated}")

    @admin.action(description=_("Дублировать"))
    def duplicate_selected(self, request, qs):
        count = 0
        for obj in qs:
            old_pk = obj.pk
            obj.pk = None
            obj.slug = ""           # чтобы пересоздался в save()
            obj.title_full = f"{obj.title_full} (копия)"
            obj.title_short = f"{obj.title_short}-copy"
            obj.is_published = False
            obj.save()
            count += 1
        self.message_user(request, f"Создано копий: {count}")

    @admin.action(description=_("Экспортировать в CSV"))
    def export_csv(self, request, qs):
        import csv
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="trips.csv"'
        w = csv.writer(resp)
        w.writerow(["Название", "Страна", "Даты", "Цена USD", "Свободно", "Статус"])
        for t in qs:
            label, _ = _state_label(t)
            dates = f"{t.date_start:%Y-%m-%d}–{t.date_end:%Y-%m-%d}" if t.date_start and t.date_end else ""
            w.writerow([t.title_full, t.country.name, dates, f"{t.price_usd}", t.seats_left, label])
        return resp
