# Скрипт для генерации .env файла

echo "🚀 Генерация .env файла для HabitFlow API"
echo "========================================"

# Проверяем, существует ли .env
if [ -f .env ]; then
    echo "⚠️  Файл .env уже существует."
    read -p "Перезаписать? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отмена."
        exit 1
    fi
fi

# Генерация секретного ключа Django
DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")

# Генерация паролей
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+' | head -c 24)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+' | head -c 24)

# Запрос данных у пользователя
read -p "Введите DEBUG режим (True/False) [True]: " DEBUG
DEBUG=${DEBUG:-True}

read -p "Введите имя базы данных [habitflow_db]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-habitflow_db}

read -p "Введите пользователя PostgreSQL [habitflow_user]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-habitflow_user}

read -p "Введите Telegram Bot Token (или оставьте пустым): " TELEGRAM_BOT_TOKEN

# Создание .env файла
cat > .env << EOF
# ============================================
# СГЕНЕРИРОВАНО АВТОМАТИЧЕСКИ $(date)
# ============================================

# Docker
COMPOSE_PROJECT_NAME=habitflow
COMPOSE_PROFILES=full

# Django
DEBUG=${DEBUG}
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
ALLOWED_HOSTS=localhost,127.0.0.1,habitflow-web,nginx
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# PostgreSQL
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

# Telegram
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_BOT_USERNAME=
TELEGRAM_WEBHOOK_URL=http://nginx/api/telegram/webhook/

# Настройки приложения
JWT_ACCESS_TOKEN_LIFETIME=86400
JWT_REFRESH_TOKEN_LIFETIME=604800
HABIT_MAX_DURATION=120
HABIT_MAX_BREAK_DAYS=7
DEFAULT_PAGE_SIZE=5
MAX_PAGE_SIZE=50

# Другое
TIME_ZONE=Europe/Moscow
LANGUAGE_CODE=ru-ru
DJANGO_SETTINGS_MODULE=config.settings
PYTHONUNBUFFERED=1
EOF

echo "✅ Файл .env успешно создан!"
echo "📁 Проверьте и отредактируйте при необходимости:"
ls -la .env