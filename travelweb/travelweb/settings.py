# travelweb/settings.py
from pathlib import Path
import os

# ========== БАЗА ==========
BASE_DIR = Path(__file__).resolve().parent.parent

# Не хардкодь ключ в проде: можно положить в .env (переменная SECRET_KEY)
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-3n4(6s!m(=h)odg%%+r2d1aayibs7o1qbud-%qtfgnhyd7)wjw",
)

# Прод
DEBUG = False

ALLOWED_HOSTS = [
    "travel.ayolclub.uz",
    ".ayolclub.uz",   # разрешим любые поддомены, на всякий (www, travel1 и т.д.)
    "localhost",
    "127.0.0.1",
]

# Для Django 4+: со схемой!
CSRF_TRUSTED_ORIGINS = [
    "https://travel.ayolclub.uz",
]

# Если за Nginx/проксей — говорим Django, что клиент за HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Безопасные cookies под HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ========== ПРИЛОЖЕНИЯ ==========
INSTALLED_APPS = [
    "jazzmin",                 # всегда первым
    "fontawesomefree",         # ← добавь это
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cities_light",
    "travelapp",
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
# URL’ы
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Откуда collectstatic соберёт файлы (если есть папка static в проекте)
STATICFILES_DIRS = [BASE_DIR / "static"]

# Куда collectstatic складывает итог (раздаёт Nginx)
STATIC_ROOT = Path("/var/www/travel_staticfiles")
MEDIA_ROOT = Path("/var/www/travel_media")

# ========== АВТО-ИД ==========
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== LOGIN FLOW ==========
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "profile"
LOGOUT_REDIRECT_URL = "login"

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

    "search_model": ["travelapp.Trip", "travelapp.Country", "travelapp.City"],
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
        "travelapp.city": "fas fa-city",
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
    "http://download.geonames.org/export/dump/cities1000.zip",
]
