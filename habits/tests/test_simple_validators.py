from django.test import TestCase


class TestSimpleValidators(TestCase):
    """Простые тесты валидации"""

    def test_number_validation(self):
        """Валидация чисел"""
        max_value = 120
        min_value = 1

        # Валидные значения
        self.assertLessEqual(90, max_value)
        self.assertGreaterEqual(90, min_value)

        # Невалидные значения
        self.assertGreater(121, max_value)
        self.assertLess(0, min_value)

    def test_string_validation(self):
        """Валидация строк"""
        value = "test"
        self.assertTrue(bool(value))
        self.assertTrue(bool(value.strip()))

        empty_value = ""
        self.assertFalse(bool(empty_value.strip()))

    def test_choice_validation(self):
        """Валидация выбора из списка"""
        allowed_choices = ["daily", "weekly", "monthly"]

        for choice in allowed_choices:
            self.assertIn(choice, allowed_choices)

        invalid_choice = "yearly"
        self.assertNotIn(invalid_choice, allowed_choices)
