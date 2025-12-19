from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from habits.validators import validate_duration, validate_frequency_choice


class TestValidatorsComplete(TestCase):
    """Тесты для оставшихся строк в validators.py"""

    def test_validate_duration_edge_cases(self):
        """Тест граничных случаев для валидации длительности"""
        # Максимальное значение
        max_duration = settings.HABIT_VALIDATION["MAX_DURATION_SECONDS"]

        try:
            validate_duration(max_duration)  # Должно пройти
            self.assertTrue(True)
        except ValidationError:
            self.fail(
                f"validate_duration не должна падать на максимальном значении {max_duration}"
            )

        # Граничное значение (максимум + 1)
        with self.assertRaises(ValidationError) as context:
            validate_duration(max_duration + 1)

        self.assertIn(str(max_duration), str(context.exception))

    def test_validate_duration_positive(self):
        """Тест положительных значений"""
        try:
            validate_duration(1)  # Минимальное положительное
            validate_duration(60)  # 1 минута
            self.assertTrue(True)
        except ValidationError:
            self.fail("validate_duration не должна падать на положительных значениях")

    def test_validate_frequency_choice_all_options(self):
        """Тест всех допустимых вариантов частоты"""
        allowed_frequencies = settings.HABIT_VALIDATION["ALLOWED_FREQUENCIES"]

        for frequency in allowed_frequencies.keys():
            try:
                validate_frequency_choice(frequency)
                self.assertTrue(True)
            except ValidationError:
                self.fail(f"Частота '{frequency}' должна быть допустимой")

        # Неправильная частота
        with self.assertRaises(ValidationError) as context:
            validate_frequency_choice("yearly")

        self.assertIn("Недопустимая периодичность", str(context.exception))

    def test_validator_functions_exist(self):
        """Тест, что все функции валидации существуют"""
        from habits.validators import (
            validate_completion_frequency,
            validate_habit_consistency,
            validate_too_frequent_completion,
        )

        # Просто проверяем, что функции можно импортировать
        self.assertTrue(callable(validate_habit_consistency))
        self.assertTrue(callable(validate_completion_frequency))
        self.assertTrue(callable(validate_too_frequent_completion))
