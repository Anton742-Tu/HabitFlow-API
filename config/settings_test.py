"""
Настройки для тестов в CI/CD
"""

from .settings import *

# Используем тестовую базу данных
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "test_habitflow_db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres_password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": "test_habitflow_db",
        },
    }
}

# Отключаем отладочные функции
DEBUG = False

# Ускоряем тесты
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Отключаем кеширование для тестов
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Отключаем внешние зависимости
TELEGRAM_BOT_TOKEN = "test_token"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
