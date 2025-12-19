from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit, HabitCompletion
from habits.serializers import HabitCompletionSerializer

User = get_user_model()


class HabitCompletionSerializerTest(TestCase):
    """Тесты для сериализатора выполнения привычек"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(9, 0),
            action="Утренняя зарядка",
            duration=60,
            frequency="daily",
        )

        self.completion = HabitCompletion.objects.create(
            habit=self.habit,
            completed_at=datetime.now(),
            is_completed=True,
            note="Тестовое выполнение",
        )

    def test_completion_serializer(self):
        """Тест сериализатора выполнения"""
        serializer = HabitCompletionSerializer(self.completion)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("habit", data)
        self.assertIn("completed_at", data)
        self.assertIn("is_completed", data)
        self.assertIn("note", data)

        self.assertEqual(data["is_completed"], True)
        self.assertEqual(data["note"], "Тестовое выполнение")

    def test_completion_serializer_validation(self):
        """Тест валидации сериализатора выполнения"""
        serializer = HabitCompletionSerializer(
            data={
                "habit": self.habit.id,
                "completed_at": datetime.now().isoformat(),
                "is_completed": True,
                "note": "Новое выполнение",
            }
        )

        self.assertTrue(serializer.is_valid())

        # Проверяем с неправильным habit_id
        serializer = HabitCompletionSerializer(
            data={
                "habit": 99999,  # Несуществующий ID
                "completed_at": datetime.now().isoformat(),
                "is_completed": True,
                "note": "Новое выполнение",
            }
        )

        self.assertFalse(serializer.is_valid())
