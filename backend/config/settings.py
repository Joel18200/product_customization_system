"""
Django settings for the Product Customization System.

Uses environment variables for production configuration with sensible
development defaults. Supports both PostgreSQL (production) and SQLite (dev).
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Load environment variables from a local .env file (if present) so that
# configuration such as database credentials is picked up without having to
# export them in the shell. Real environment variables always take precedence
# (setdefault never overrides an already-set value).
def _load_dotenv(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass


_load_dotenv(BASE_DIR / ".env")


# Environment helpers
def env(key, default=None):
    return os.environ.get(key, default)

def env_bool(key, default=False):
    return os.environ.get(key, str(default)).lower() in ("true", "1", "yes")

def env_int(key, default=0):
    return int(os.environ.get(key, default))

def env_list(key, default=""):
    val = os.environ.get(key, default)
    return [s.strip() for s in val.split(",") if s.strip()]


# SECURITY
SECRET_KEY = env("SECRET_KEY", "django-insecure-qy9bmd)92_9+jsoo0dvz*!l%37-*0*nr&m@+hi=)3e$b&2ayu@")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# In development, accept requests for any host (e.g. the machine's LAN IP)
# so the app is reachable via the "Network" URL, not just localhost.
# Production must set ALLOWED_HOSTS explicitly (DEBUG=False).
if DEBUG:
    ALLOWED_HOSTS = ["*"]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_celery_results",
    "django_celery_beat",

    # Our Apps
    "accounts",
    "products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# Use PostgreSQL in production, SQLite as fallback for local dev
DB_ENGINE = env("DB_ENGINE", "django.db.backends.sqlite3")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": env("DB_NAME", "customization_db"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", "postgres"),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
            "OPTIONS": {
                "connect_timeout": 10,
                # Render (and most managed Postgres) require SSL for external
                # connections. Defaults to "prefer"; set DB_SSLMODE=require in
                # .env for hosts that mandate SSL.
                "sslmode": env("DB_SSLMODE", "prefer"),
            },
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ──────────────────────────────────────────────
# Django REST Framework
# ──────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}


# ──────────────────────────────────────────────
# JWT Configuration
# ──────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 60)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ──────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
)
CORS_ALLOW_CREDENTIALS = True

# In development, also allow the frontend served from any LAN IP (the
# "Network" URL). Uses regexes so the specific origin is echoed back and
# credentialed requests keep working. Not applied in production.
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
        r"^http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$",
        r"^http://192\.168\.\d{1,3}\.\d{1,3}:\d+$",
        r"^http://172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}:\d+$",
    ]
    # Mirror trusted origins for CSRF (session-authenticated POSTs).
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


# ──────────────────────────────────────────────
# Celery Configuration
# ──────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"


# ──────────────────────────────────────────────
# Redis Cache
# ──────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use Redis cache if available
if REDIS_URL and not DEBUG:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 300,
    }


# ──────────────────────────────────────────────
# OpenAPI / Swagger (drf-spectacular)
# ──────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Product Customization System API",
    "DESCRIPTION": "High-performance product customization platform with realistic rendering",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
}


# ──────────────────────────────────────────────
# File Upload Settings
# ──────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = env_int("MAX_UPLOAD_SIZE_MB", 20)
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
ALLOWED_IMAGE_TYPES = env_list(
    "ALLOWED_IMAGE_TYPES",
    "image/png,image/jpeg,image/webp"
)

# Django file upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE


# ──────────────────────────────────────────────
# Rendering Pipeline Settings
# ──────────────────────────────────────────────
PREVIEW_MAX_DIMENSION = env_int("PREVIEW_MAX_DIMENSION", 1200)
FINAL_RENDER_MAX_DIMENSION = env_int("FINAL_RENDER_MAX_DIMENSION", 4000)
RENDER_QUALITY = env_int("RENDER_QUALITY", 95)


# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "products": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
