FROM python:3.12-slim

# Устанавливаем системные зависимости ВКЛЮЧАЯ NGINX
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Копируем все скрипты
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.py 2>/dev/null || true

# Копируем nginx конфиг
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Собираем статические файлы Django
RUN python manage.py collectstatic --noinput

EXPOSE 80 8000

# Устанавливает переменные окружения
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PYTHONPATH=/app

# Запускаем Nginx и Gunicorn
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
