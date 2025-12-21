"""
Create test data for CI/CD pipeline
"""

import os
import sys
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

django.setup()

from django.contrib.auth import get_user_model

from habits.models import Habit
from telegram_bot.models import TelegramConnectionCode, TelegramUser

User = get_user_model()


def create_test_data():
    print("🧪 Создание тестовых данных для CI...")

    # Создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username="testuser", defaults={"email": "test@example.com", "is_active": True}
    )
    if created:
        user.set_password("testpass123")
        user.save()
        print(f"✅ Создан тестовый пользователь: {user.username}")
    else:
        print(f"✅ Тестовый пользователь уже существует: {user.username}")

    # Создаем тестовую привычку
    habit, created = Habit.objects.get_or_create(
        user=user,
        place="Дом",
        time="09:00",
        action="Пить стакан воды",
        defaults={
            "duration": 60,
            "frequency": "daily",
            "is_public": True,
            "is_pleasant": False,
        },
    )
    if created:
        print(f"✅ Создана тестовая привычка: {habit.action}")
    else:
        print(f"✅ Тестовая привычка уже существует: {habit.action}")

    # Создаем Telegram данные
    tg_user, created = TelegramUser.objects.get_or_create(
        user=user,
        defaults={
            "chat_id": 123456789,
            "telegram_username": "testuser_tg",
            "is_active": True,
        },
    )
    if created:
        print(f"✅ Создан Telegram пользователь: {tg_user.telegram_username}")

    # Создаем код подключения
    code, created = TelegramConnectionCode.objects.get_or_create(
        user=user,
        defaults={
            "code": "TEST123",
            "expires_at": datetime.now() + timedelta(hours=1),
            "is_used": False,
        },
    )
    if created:
        print(f"✅ Создан код подключения: {code.code}")

    print("✅ Тестовые данные созданы успешно!")

    # Выводим статистику
    print("\n📊 Статистика базы данных:")
    print(f"   Пользователей: {User.objects.count()}")
    print(f"   Привычек: {Habit.objects.count()}")
    print(f"   Telegram пользователей: {TelegramUser.objects.count()}")
    print(f"   Кодов подключения: {TelegramConnectionCode.objects.count()}")


if __name__ == "__main__":
    create_test_data()
