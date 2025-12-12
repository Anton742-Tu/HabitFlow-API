from django.test import TestCase


class TestScriptsBasic(TestCase):
    def test_scripts_module(self):
        """Тест модуля scripts"""
        import scripts
        self.assertTrue(hasattr(scripts, '__file__'))

    def test_directory_exists(self):
        """Тест, что директория scripts существует"""
        import os
        import scripts

        scripts_dir = os.path.dirname(scripts.__file__)
        self.assertTrue(os.path.exists(scripts_dir))
        self.assertTrue(os.path.isdir(scripts_dir))