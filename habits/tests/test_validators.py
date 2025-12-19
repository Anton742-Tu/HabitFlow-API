from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from habits.models import Habit
from habits.validators import validate_duration, validate_habit_consistency

User = get_user_model()


class ValidatorsTestCase(TestCase):
    """Тесты для валидаторов"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_validate_duration(self):
        """Тест валидации времени выполнения"""
        # Корректное значение
        try:
            validate_duration(120)
        except ValidationError:
            self.fail("validate_duration вызвала ValidationError для значения 120")

        # Слишком большое значение
        with self.assertRaises(ValidationError):
            validate_duration(121)

        # Нулевое значение
        with self.assertRaises(ValidationError):
            validate_duration(0)

        # Отрицательное значение
        with self.assertRaises(ValidationError):
            validate_duration(-10)

    def test_validate_habit_consistency(self):
        """Тест валидации согласованности привычки"""
        # Создаем приятную привычку
        pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Диван",
            time=time(20, 0),
            action="Приятная привычка",
            duration=60,
            is_pleasant=True,
        )

        # Тест 1: Приятная привычка с вознаграждением (должна быть ошибка)
        habit_with_reward = Habit(
            user=self.user,
            place="Дом",
            time=time(8, 0),
            action="Тест",
            duration=60,
            is_pleasant=True,
            reward="Шоколадка",
        )

        with self.assertRaises(ValidationError):
            validate_habit_consistency(habit_with_reward)

        # Тест 2: Полезная привычка с и reward и related_habit (должна быть ошибка)
        habit_with_both = Habit(
            user=self.user,
            place="Дом",
            time=time(8, 0),
            action="Тест",
            duration=60,
            is_pleasant=False,
            reward="Награда",
            related_habit=pleasant_habit,
        )

        with self.assertRaises(ValidationError):
            validate_habit_consistency(habit_with_both)

        # Тест 3: Корректная привычка с reward (без ошибки)
        habit_correct_with_reward = Habit(
            user=self.user,
            place="Дом",
            time=time(8, 0),
            action="Тест",
            duration=60,
            is_pleasant=False,
            reward="Награда",
        )

        try:
            validate_habit_consistency(habit_correct_with_reward)
        except ValidationError:
            self.fail("Корректная привычка вызвала ошибку валидации")
