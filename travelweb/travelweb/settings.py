# travelweb/settings.py
from pathlib import Path
import os

# ---- env ----
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ========== БАЗА ==========
# Не хардкодь ключ в проде: можно положить в .env (переменная SECRET_KEY)
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-3n4(6s!m(=h)odg%%+r2d1aayibs7o1qbud-%qtfgnhyd7)wjw",
)

# Прод
DEBUG = False

ALLOWED_HOSTS = [
    "travel.ayolclub.uz",
    ".ayolclub.uz",   # разрешим любые поддомены (www и т.п.)
    "localhost",
    "127.0.0.1",
]

# Для Django 4+: со схемой!
CSRF_TRUSTED_ORIGINS = [
    "https://travel.ayolclub.uz",
    "https://ayolclub.uz",
    "https://www.ayolclub.uz",
]

# Если за Nginx/проксей — говорим Django, что клиент за HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Безопасные cookies под HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ========== ПРИЛОЖЕНИЯ ==========
INSTALLED_APPS = [
    "jazzmin",                 # всегда первым
    "fontawesomefree",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cities_light",
    "travelapp",
    "accounts",  # для регистрации/входа
]

# ========== MIDDLEWARE ==========
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

# ========== ШАБЛОНЫ ==========
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# ========== БД ==========
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ========== ПАРОЛИ ==========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========== ЛОКАЛИ ==========
LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# ========== СТАТИКА/МЕДИА ==========
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "staticfiles"]
STATIC_ROOT = Path("/var/www/travel_staticfiles")
MEDIA_ROOT = Path("/var/www/travel_media")

# ========== АВТО-ИД ==========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== LOGIN FLOW ==========
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "profile"
LOGOUT_REDIRECT_URL = "login"

# ========== EMAIL (для отправки кода) ==========
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "in-v3.mailjet.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@travel.ayolclub.uz")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ========== JAZZMIN ==========
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

# ========== CITIES-LIGHT ==========
CITIES_LIGHT_TRANSLATION_LANGUAGES = ["ru", "en"]
CITIES_LIGHT_CITY_SOURCES = [
    "https://download.geonames.org/export/dump/cities1000.zip",
]
