FROM python:3.11-slim

# Устанавливаем зависимости для PostgreSQL
RUN apt-get update \
    && apt-get install -y gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Собираем статические файлы (будет выполнено позже)
# RUN python manage.py collectstatic --noinput

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["gunicorn", "habitflow.wsgi:application", "--bind", "0.0.0.0:8000"]