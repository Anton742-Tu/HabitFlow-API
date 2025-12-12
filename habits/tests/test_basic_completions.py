from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit, HabitCompletion

User = get_user_model()


class BasicHabitCompletionTest(TestCase):
    """Базовые тесты выполнения привычек"""

    def test_basic_completion_creation(self):
        """Базовый тест создания выполнения"""
        user = User.objects.create_user(username="test", password="test")

        habit = Habit.objects.create(
            user=user, place="Дом", time=time(9, 0), action="Базовая привычка", frequency="daily", duration=60
        )

        completion = HabitCompletion.objects.create(
            habit=habit, completed_at=datetime.now(), is_completed=True, note="Базовое выполнение"
        )

        self.assertIsNotNone(completion.id)
        self.assertEqual(completion.habit, habit)
        print(f"✅ Базовый тест: создано выполнение {completion.id}")

    def test_completion_fields(self):
        """Тест полей выполнения"""
        user = User.objects.create_user(username="user1", password="pass1")

        habit = Habit.objects.create(
            user=user, place="Офис", time=time(14, 0), action="Работа стоя", frequency="weekly", duration=120
        )

        note_text = "Важное выполнение с заметкой"
        completion = HabitCompletion.objects.create(
            habit=habit, completed_at=datetime.now(), is_completed=False, note=note_text  # Не выполнено
        )

        self.assertEqual(completion.note, note_text)
        self.assertFalse(completion.is_completed)
        print(f"✅ Проверка полей: note='{completion.note}', is_completed={completion.is_completed}")
