from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit

User = get_user_model()


class CorrectHabitModelTest(TestCase):
    """Исправленные тесты модели Habit"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_habit_with_all_fields(self):
        """Тест создания привычки со всеми полями"""
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(9, 0),
            action="Пить воду утром",
            is_pleasant=False,
            frequency="daily",
            duration=60,
            is_public=True,
        )

        self.assertEqual(habit.action, "Пить воду утром")
        self.assertEqual(habit.place, "Дом")
        self.assertEqual(habit.duration, 60)
        self.assertEqual(habit.frequency, "daily")
        self.assertFalse(habit.is_pleasant)
        self.assertTrue(habit.is_public)
        self.assertIsNotNone(habit.created_at)
        self.assertIsNotNone(habit.updated_at)

        # Проверяем строковое представление
        habit_str = str(habit)
        print(f"Строковое представление: '{habit_str}'")

        # Основные проверки
        self.assertIn("Пить воду", habit_str or "")
        self.assertIn("testuser", habit_str.lower() or "")
