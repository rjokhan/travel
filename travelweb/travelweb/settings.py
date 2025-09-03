# travelweb/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# ========= BASE / ENV =========
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ========= CORE =========
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-3n4(6s!m(=h)odg%%+r2d1aayibs7o1qbud-%qtfgnhyd7)wjw",
)

# можно переключать через .env: DEBUG=True/False
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "travel.ayolclub.uz",
    ".ayolclub.uz",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://travel.ayolclub.uz",
    "https://ayolclub.uz",
    "https://www.ayolclub.uz",
    "https://*.ayolclub.uz",
]

# ---- прокси/https ----
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ---- cookie / сессии ----
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ВАЖНО: чтобы сессия была видна на основном сайте после callback
# (если когда-нибудь дернём колбэк/поддомены), закрепляем на базовый домен
SESSION_COOKIE_DOMAIN = ".ayolclub.uz"
CSRF_COOKIE_DOMAIN = ".ayolclub.uz"

# Доп. защита (не мешает авторизации)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ========= APPS =========
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cities_light",
    "travelapp",
    "accounts",
]

# ========= MIDDLEWARE =========
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

# ========= TEMPLATES =========
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "travelweb.wsgi.application"

# ========= DATABASE =========
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ========= PASSWORDS =========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========= I18N / TZ =========
LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# ========= STATIC / MEDIA =========
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# каталоги с исходниками статики (откуда collectstatic собирает)
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "staticfiles",
]
# куда collectstatic складывает итоговую статику (Nginx отдаёт отсюда)
STATIC_ROOT = Path("/var/www/travel_staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========= LOGIN FLOW =========
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "profile"
LOGOUT_REDIRECT_URL = "login"

# ========= TELEGRAM LOGIN =========
# В .env укажите TELEGRAM_BOT_TOKEN и TELEGRAM_BOT_NAME
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "travel_ayolclub_bot")  # без @

# ========= EMAIL =========
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "in-v3.mailjet.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@travel.ayolclub.uz")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ========= JAZZMIN =========
JAZZMIN_SETTINGS = {
    "site_title": "A CLUB TRAVEL — Админка",
    "site_header": "A CLUB TRAVEL",
    "site_brand": "A CLUB TRAVEL",
    "welcome_sign": "Добро пожаловать! Управление путешествиями и бронированиями",
    "copyright": "© A CLUB",
    "site_logo": "admin/brand/logo-white.svg",
    "login_logo": "admin/brand/logo-mark.svg",
    "login_logo_dark": "admin/brand/logo-white.svg",
    "search_model": ["travelapp.Trip", "travelapp.Country"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Панель", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"app": "travelapp"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["travelapp", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "travelapp": "fas fa-route",
        "travelapp.country": "fas fa-flag",
        "travelapp.trip": "fas fa-suitcase-rolling",
    },
    "custom_css": "admin/override.css",
    "custom_js": None,
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

# ========= CITIES-LIGHT =========
CITIES_LIGHT_TRANSLATION_LANGUAGES = ["ru", "en"]
CITIES_LIGHT_CITY_SOURCES = [
    "https://download.geonames.org/export/dump/cities1000.zip",
]

# ========= LOGGING =========
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "accounts": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "travelapp": {"handlers": ["console"], "level": "INFO", "propagate": True},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": True},
    },
}
