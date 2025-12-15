FROM python:3.11-slim as builder

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем pip и зависимости
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Финальный образ
# ============================================
FROM python:3.11-slim

# Устанавливаем только runtime зависимости
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создаем пользователя
RUN useradd -m -u 1000 -s /bin/bash django

WORKDIR /app

# Копируем код проекта
COPY --chown=django:django . .

# Создаем директории
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app

USER django

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]