from django.test import TestCase


class TestUtilsBasic(TestCase):
    def test_utils_import(self):
        """Тест импорта utils"""
        try:
            from habits import utils
            self.assertTrue(True)
        except ImportError:
            self.fail("Не удалось импортировать habits.utils")