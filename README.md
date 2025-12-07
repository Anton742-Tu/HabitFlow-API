# 🚀 HabitFlow API

**HabitFlow API** — это RESTful API для трекера полезных привычек, основанный на методологии **Atomic Habits** (Джеймс Клир). Позволяет пользователям создавать, отслеживать и анализировать свои привычки с соблюдением всех правил из книги.

[![Django](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-blue.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![JWT](https://img.shields.io/badge/JWT-Auth-orange.svg)](https://jwt.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Возможности

- ✅ **JWT аутентификация** (регистрация, вход, обновление токенов)
- ✅ **CRUD операции** с привычками
- ✅ **Пагинация** (5 привычек на страницу, настраивается)
- ✅ **Публичные/приватные привычки**
- ✅ **Отслеживание выполнения** привычек
- ✅ **Валидация** по всем правилам Atomic Habits
- ✅ **Swagger/ReDoc документация**
- ✅ **PostgreSQL поддержка**
- ✅ **Docker контейнеризация**
- ✅ **Полное покрытие тестами**

## 📋 Правила валидации (Atomic Habits)

1. ⏱️ **Время выполнения ≤ 120 секунд** — привычка не должна занимать больше 2 минут
2. ❌ **Нельзя одновременно указывать и связанную привычку и вознаграждение**
3. 😊 **Связанные привычки должны быть приятными** — только приятные привычки могут быть связанными
4. 🎯 **У приятной привычки не может быть вознаграждения или связанной привычки**
5. 📅 **Нельзя выполнять привычку реже 1 раза в 7 дней**
6. ⏰ **Нельзя не выполнять привычку более 7 дней**

## 🏗️ Архитектура
![img.png](img.png)

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонирование репозитория
git clone <repository-url>
cd HabitFlow-API

# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```
### 2. Настройка базы данных
#### Вариант A: SQLite (для разработки)
```bash
# Настройка .env файла
cp .env.example .env
# Отредактируйте .env: USE_POSTGRESQL=False

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
```
#### Вариант B: PostgreSQL (для production)
```sql
-- Создание базы данных
CREATE DATABASE habitflow_db;
CREATE USER habitflow_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE habitflow_db TO habitflow_user;
```
```bash
# Настройка .env
POSTGRES_DB=habitflow_db
POSTGRES_USES=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
USE_POSTGRESQL=True
```
```
# Применение миграций
python manage.py migrate
```
### 3. Запуск сервера
```bash
# Разработка
python manage.py runserver

# Production (с Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```
### 4. Создание тестовых данных
```bash
python create_test_data.py
```
## 🤖 Интеграция с Telegram

### Как подключить Telegram бота:

1. **Войдите** в веб-приложение HabitFlow
2. **Перейдите** в профиль → "Подключить Telegram"
3. **Скопируйте** код подключения
4. **Откройте** Telegram и найдите бота: @anton_tumashov_bot
5. **Отправьте** команду: `/connect ВАШ_КОД`

### Команды бота:

- `/start` - Начало работы
- `/status` - Статус подключения
- `/stats` - Ваша статистика
- `/settings` - Настройки уведомлений
- `/help` - Помощь по командам

### Что вы получите:

✅ **Напоминания** о времени выполнения привычек  
✅ **Ежедневные отчеты** о вашем прогрессе  
✅ **Уведомления** о достижениях  
✅ **Быстрый доступ** к статистике

### Для разработчиков:

- API эндпоинт для кода: `GET /api/users/telegram/connect/`
- Модели: `TelegramUser`, `TelegramConnectionCode`
- Команды: `python manage.py run_bot`, `python manage.py send_test_reminder`
## 📡 API Endpoints
### 🔐 Аутентификация
#### Метод	Эндпоинт	Описание
- POST	/api/users/register/	Регистрация нового пользователя
- POST	/api/users/token/	Получение JWT токена
- POST	/api/users/token/refresh/	Обновление токена
- POST	/api/users/logout/	Выход (blacklist refresh token)
- GET	/api/users/profile/	Профиль пользователя
- PATCH	/api/users/profile/	Обновление профиля
### 📝 Привычки
#### Метод	Эндпоинт	Описание
- GET	/api/habits/	Список привычек (пагинация)
- GET	/api/habits/my_habits/	Только мои привычки
- GET	/api/habits/public/	Публичные привычки
- POST	/api/habits/	Создать привычку
- GET	/api/habits/{id}/	Получить привычку
- PUT	/api/habits/{id}/	Обновить привычку
- PATCH	/api/habits/{id}/	Частичное обновление
- DELETE	/api/habits/{id}/	Удалить привычку
- POST	/api/habits/{id}/complete/	Отметить выполнение
- PATCH	/api/habits/{id}/toggle_public/	Переключить публичность

###  ✅ Выполнения привычек
#### Метод	Эндпоинт	Описание
- GET	/api/completions/	Список выполнений
- POST	/api/completions/	Создать выполнение
- DELETE	/api/completions/{id}/	Удалить выполнение
## 🔒 Права доступа
- Владелец привычки: Полный CRUD доступ 
- Другие пользователи: Только чтение публичных привычек 
- Неаутентифицированные: Только чтение публичных привычек

## 🧪 Примеры запросов
### Регистрация пользователя
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "securepass123",
    "password2": "securepass123"
  }'
```
### Получение токена
```bash
curl -X POST http://localhost:8000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "securepass123"
  }'
```
### Создание привычки
```bash
curl -X POST http://localhost:8000/api/habits/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "place": "Дом",
    "time": "08:00",
    "action": "Пить стакан воды",
    "duration": 60,
    "frequency": "daily",
    "is_public": true
  }'
```
### Получение привычек с пагинацией
```bash
curl -X GET "http://localhost:8000/api/habits/?page=2&page_size=3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
## 🐳 Docker развертывание
### 1. Запуск с Docker Compose
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```
### 2. Docker Compose файл
```yaml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: habitflow_db
      POSTGRES_USER: habitflow_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn habitflow.wsgi:application --bind 0.0.0.0:8000"
    environment:
      - USE_POSTGRESQL=True
      - POSTGRES_HOST=db
    depends_on:
      - db
```
## 🧪 Тестирование
```bash
# Запуск всех тестов
python manage.py test --verbosity=2

# Тесты с покрытием
coverage run manage.py test
coverage report
coverage html

# Запуск конкретных тестов
python manage.py test habits.tests
python manage.py test users.tests
```
## 📚 Документация
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/
- Админка Django: http://localhost:8000/admin/

## 🛠️ Разработка
### Установка для разработки
```bash
pip install -r requirements-dev.txt
pre-commit install
Code Quality
bash
# Форматирование кода
black .
isort .

# Проверка стиля
flake8 .

# Проверка типов
mypy .
Git Hooks
```
### Проект использует pre-commit hooks для автоматической проверки кода:

- black (форматирование)
- isort (сортировка импортов)
- flake8 (стиль кода)
- mypy (проверка типов)

## 🔧 Настройки окружения
- Основные переменные окружения (.env):
- env
### Django
- DEBUG=True
- SECRET_KEY=your-secret-key
- ALLOWED_HOSTS=localhost,127.0.0.1

### Database
- USE_POSTGRESQL=False
- POSTGRES_DB=habitflow_db
- POSTGRES_USER=habitflow_user
- POSTGRES_PASSWORD=secure_password
- POSTGRES_HOST=localhost
- POSTGRES_PORT=5432

### JWT
- JWT_ACCESS_TOKEN_LIFETIME=86400  # 1 день
- JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 дней

### Pagination
- DEFAULT_PAGE_SIZE=5
- MAX_PAGE_SIZE=50
## 📊 Модели данных
### Habit (Привычка)
```python
{
    "id": 1,
    "user": 1,
    "place": "Дом",
    "time": "08:00",
    "action": "Пить воду",
    "is_pleasant": false,
    "related_habit": null,
    "frequency": "daily",
    "reward": "",
    "duration": 60,
    "is_public": true,
    "created_at": "2024-01-15T08:00:00Z",
    "full_description": "Я буду пить воду в 08:00 в дом"
}
```
HabitCompletion (Выполнение привычки)
```python
{
    "id": 1,
    "habit": 1,
    "completed_at": "2024-01-15T08:05:00Z",
    "is_completed": true,
    "note": "Выполнено успешно!"
}
```
## 🤝 Вклад в проект
- Форкните репозиторий 
- Создайте ветку для вашей фичи (git checkout -b feature/amazing-feature)
- Закоммитьте изменения (git commit -m 'Add amazing feature')
- Запушьте ветку (git push origin feature/amazing-feature)
- Откройте Pull Request

## 📄 Лицензия
Этот проект лицензирован под MIT License - смотрите файл LICENSE для деталей.

## 👥 Авторы
- Anton-Tu - Разработчик и идейный вдохновитель 
- Джеймс Клир - Автор методологии Atomic Habits

HabitFlow API © 2024. Разработано с ❤️ для трекинга полезных привычек.