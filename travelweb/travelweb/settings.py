from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-3n4(6s!m(=h)odg%%+r2d1aayibs7o1qbud-%qtfgnhyd7)wjw'

DEBUG = True
ALLOWED_HOSTS: list[str] = []

# ====================
# Applications
# ====================
INSTALLED_APPS = [
    "jazzmin",                  # 👈 Jazzmin всегда первым
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # База стран/городов из GeoNames
    "cities_light",

    # Ваше приложение
    "travelapp",
]

# ====================
# Middleware
# ====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "travelweb.urls"

# ====================
# Templates
# ====================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # ищем в /templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "travelweb.wsgi.application"

# ====================
# Database
# ====================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ====================
# Password validators
# ====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================
# Locale
# ====================
LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ====================
# Static & Media
# ====================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]   # берём из папки /static
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====================
# Default
# ====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================
# Jazzmin settings (кастомизация админки)
# ====================
JAZZMIN_SETTINGS = {
    "site_title": "A CLUB TRAVEL — Админка",
    "site_header": "A CLUB TRAVEL",
    "site_brand": "A CLUB TRAVEL",
    "welcome_sign": "Добро пожаловать! Управление путешествиями и бронированиями",
    "copyright": "© A CLUB",

    # Логотипы (должны лежать в static/admin/brand/)
    "site_logo": "admin/brand/logo-white.svg",
    "login_logo": "admin/brand/logo-mark.svg",
    "login_logo_dark": "admin/brand/logo-white.svg",

    # Поиск в шапке админки
    "search_model": ["travelapp.Trip", "travelapp.Country", "travelapp.City"],
    "user_avatar": None,

    # Верхнее меню
    "topmenu_links": [
        {"name": "Панель", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"app": "travelapp"},
    ],

    # Сайдбар
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["travelapp", "auth"],

    # Иконки моделей
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "travelapp": "fas fa-route",
        "travelapp.country": "fas fa-flag",
        "travelapp.city": "fas fa-city",
        "travelapp.trip": "fas fa-suitcase-rolling",
    },

    # Кастомный CSS
    "custom_css": "admin/override.css",
    "custom_js": None,

    # Тема
    "theme": "darkly",
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark",
    "brand_colour": "navbar-dark",
    "accent": "accent-maroon",
    "sidebar": "sidebar-dark-maroon",
    "footer_fixed": True,
    "sidebar_nav_child_indent": True,
    "actions_sticky_top": True,
    "body_small_text": False,
    "sidebar_compact_style": False,
    "sidebar_nav_small_text": False,
}

# ====================
# django-cities-light (страны/города)
# ====================
# Языки, для которых подгружаются переводы названий (если есть)
CITIES_LIGHT_TRANSLATION_LANGUAGES = ["ru", "en"]

# Источник городов. По умолчанию возьмём cities1000 (население >1k).
# Если хочешь быстрее/меньше — замени на cities5000.zip.
CITIES_LIGHT_CITY_SOURCES = [
    "http://download.geonames.org/export/dump/cities1000.zip",
]

# (Опционально) если будет много данных и SQLite тормозит — переходи на PostgreSQL.
