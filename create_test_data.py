import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habitflow.settings")
django.setup()

from datetime import time

from django.contrib.auth import get_user_model

from habits.models import Habit

User = get_user_model()

print("Создание тестовых данных...")

# Создаем тестовых пользователей
users_data = [
    {"username": "alex", "email": "alex@example.com", "password": "alex123"},
    {"username": "maria", "email": "maria@example.com", "password": "maria123"},
    {"username": "demo", "email": "demo@example.com", "password": "demo123"},
]

for user_data in users_data:
    user, created = User.objects.get_or_create(username=user_data["username"], email=user_data["email"])
    if created:
        user.set_password(user_data["password"])
        user.save()
        print(f"✅ Пользователь создан: {user.username}")

# Создаем тестовые привычки
habits_data = [
    {
        "user": "alex",
        "action": "Утренняя зарядка",
        "place": "Дом",
        "time": "07:00",
        "duration": 60,
        "frequency": "daily",
        "is_public": True,
        "is_pleasant": False,
    },
    {
        "user": "alex",
        "action": "Чтение книги",
        "place": "Диван",
        "time": "21:00",
        "duration": 30,
        "frequency": "daily",
        "is_public": False,
        "is_pleasant": False,
    },
    {
        "user": "maria",
        "action": "Пробежка в парке",
        "place": "Парк",
        "time": "08:00",
        "duration": 120,
        "frequency": "weekly",
        "is_public": True,
        "is_pleasant": False,
    },
    {
        "user": "maria",
        "action": "Медитация",
        "place": "Комната",
        "time": "07:30",
        "duration": 15,
        "frequency": "daily",
        "is_public": True,
        "is_pleasant": True,
    },
    {
        "user": "demo",
        "action": "Изучение английского",
        "place": "Кафе",
        "time": "18:00",
        "duration": 45,
        "frequency": "daily",
        "is_public": True,
        "is_pleasant": False,
    },
    {
        "user": "demo",
        "action": "Планирование дня",
        "place": "Офис",
        "time": "09:00",
        "duration": 10,
        "frequency": "daily",
        "is_public": False,
        "is_pleasant": False,
    },
]

for habit_data in habits_data:
    user = User.objects.get(username=habit_data["user"])

    # Проверяем не существует ли уже привычка
    if not Habit.objects.filter(user=user, action=habit_data["action"]).exists():
        hours, minutes = map(int, habit_data["time"].split(":"))

        habit = Habit.objects.create(
            user=user,
            place=habit_data["place"],
            time=time(hours, minutes),
            action=habit_data["action"],
            duration=habit_data["duration"],
            frequency=habit_data["frequency"],
            is_public=habit_data["is_public"],
            is_pleasant=habit_data["is_pleasant"],
        )
        print(f"✅ Привычка создана: {habit.action} ({habit_data['user']})")

print("\n" + "=" * 50)
print("✅ Тестовые данные созданы!")
print("=" * 50)
print(f"Пользователей: {User.objects.count()}")
print(f"Привычек: {Habit.objects.count()}")
print(f"Публичных привычек: {Habit.objects.filter(is_public=True).count()}")
print(f"Приятных привычек: {Habit.objects.filter(is_pleasant=True).count()}")
