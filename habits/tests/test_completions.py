from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from habits.models import Habit, HabitCompletion

User = get_user_model()


class FinalHabitCompletionTest(TestCase):
    """Финальные тесты для модели выполнения привычек"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Создаем привычку
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(9, 0),
            action="Утренняя зарядка",
            is_pleasant=False,
            frequency="daily",  # Можно выполнять раз в день
            duration=60,
            is_public=True,
        )

    def test_create_completion_success(self):
        """Тест успешного создания выполнения"""
        completion = HabitCompletion.objects.create(
            habit=self.habit,
            completed_at=datetime.now(),
            is_completed=True,
            note="Выполнено успешно",
        )

        self.assertEqual(completion.habit, self.habit)
        self.assertTrue(completion.is_completed)
        self.assertEqual(completion.note, "Выполнено успешно")
        self.assertIsNotNone(completion.completed_at)
        print(f"✅ Создано выполнение с ID: {completion.id}")

    def test_completion_string_representation(self):
        """Тест строкового представления выполнения"""
        completion = HabitCompletion.objects.create(
            habit=self.habit,
            completed_at=datetime.now(),
            is_completed=True,
            note="Тестовое выполнение",
        )

        completion_str = str(completion)
        print(f"Строковое представление выполнения: '{completion_str}'")

        # Проверяем что строка не пустая
        self.assertIsNotNone(completion_str)
        self.assertGreater(len(completion_str), 0)

        # Может содержать символ выполнения или название привычки
        has_expected_content = any(
            [
                "✓" in completion_str,
                "Утренняя зарядка" in completion_str,
                "зарядка" in completion_str.lower(),
            ]
        )
        self.assertTrue(
            has_expected_content,
            f"Строка не содержит ожидаемых элементов: {completion_str}",
        )

    def test_single_completion_only(self):
        """Тест только одного выполнения (без проверки связи)"""
        completion = HabitCompletion.objects.create(
            habit=self.habit,
            completed_at=datetime.now(),
            is_completed=True,
            note="Единственное выполнение",
        )

        self.assertEqual(completion.habit, self.habit)
        print("✅ Создано одно выполнение")

    def test_completion_with_false_status(self):
        """Тест выполнения с статусом невыполнено"""
        completion = HabitCompletion.objects.create(
            habit=self.habit,
            completed_at=datetime.now(),
            is_completed=False,
            note="Пропущено",
        )

        self.assertFalse(completion.is_completed)
        self.assertEqual(completion.note, "Пропущено")
        print("✅ Создано выполнение со статусом 'не выполнено'")
