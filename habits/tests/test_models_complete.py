from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit, HabitCompletion

User = get_user_model()


class TestModelsComplete(TestCase):
    """Тесты для оставшихся строк в models.py"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.habit = Habit.objects.create(user=self.user, action="Test Action", time="09:00:00", place="Home")

    def test_habit_completion_creation(self):
        """Тест создания выполнения привычки"""
        completion = HabitCompletion.objects.create(habit=self.habit, is_completed=True, note="Тестовое выполнение")

        self.assertEqual(completion.habit, self.habit)
        self.assertTrue(completion.is_completed)
        self.assertEqual(completion.note, "Тестовое выполнение")
        self.assertIsNotNone(completion.completed_at)

    def test_habit_str_method(self):
        """Тест строкового представления привычки"""
        str_repr = str(self.habit)

        # Проверяем, что строка содержит нужную информацию
        self.assertIn("Test Action", str_repr)
        self.assertIn("09:00:00", str_repr)

    def test_habit_duration_default(self):
        """Тест значения по умолчанию для duration"""
        # Проверяем, что duration установлен
        self.assertEqual(self.habit.duration, 120)  # Или другое значение по умолчанию

    def test_habit_public_default(self):
        """Тест значения по умолчанию для is_public"""
        self.assertFalse(self.habit.is_public)
