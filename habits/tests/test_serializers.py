from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit
from habits.serializers import HabitSerializer, PublicHabitSerializer

User = get_user_model()


class SerializersTestCase(TestCase):
    """Тесты для сериализаторов"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.habit_data = {
            "user": self.user,
            "place": "Дом",
            "time": time(8, 0),
            "action": "Тестовая привычка",
            "is_pleasant": False,
            "frequency": "daily",
            "duration": 60,
            "is_public": True,
        }

        self.habit = Habit.objects.create(**self.habit_data)

    def test_habit_serializer(self):
        """Тест сериализатора HabitSerializer"""
        serializer = HabitSerializer(self.habit)

        data = serializer.data

        self.assertEqual(data["action"], "Тестовая привычка")
        self.assertEqual(data["place"], "Дом")
        self.assertEqual(data["duration"], 60)
        self.assertEqual(data["is_public"], True)
        self.assertIn("full_description", data)
        self.assertIn("user", data)

    def test_habit_serializer_validation(self):
        """Тест валидации в HabitSerializer"""
        # Тест с некорректной длительностью (> 120 секунд)
        invalid_data = {"place": "Дом", "time": "08:00", "action": "Тест", "duration": 130}  # > 120

        serializer = HabitSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("duration", serializer.errors)

    def test_public_habit_serializer(self):
        """Тест сериализатора PublicHabitSerializer"""
        serializer = PublicHabitSerializer(self.habit)

        data = serializer.data

        # PublicHabitSerializer должен содержать ограниченный набор полей
        self.assertEqual(data["action"], "Тестовая привычка")
        self.assertEqual(data["place"], "Дом")
        self.assertEqual(data["is_public"], True)
        self.assertIn("full_description", data)

        # Не должно быть полей reward и related_habit в публичном сериализаторе
        self.assertNotIn("reward", data)
        self.assertNotIn("related_habit", data)
