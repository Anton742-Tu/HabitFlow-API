FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Копируем все скрипты
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.py

EXPOSE 8000

CMD ["sh", "-c", "python /scripts/wait_for_db.py && python manage.py migrate && python /scripts/create_superuser.py && python manage.py runserver 0.0.0.0:8000"]

# Устанавливает переменную окружения, которая гарантирует, что вывод из python будет отправлен прямо в терминал без предварительной буферизации
ENV PYTHONUNBUFFERED 1