from django.conf import settings
from django.test import TestCase


class TestSettings(TestCase):
    def test_required_settings(self):
        """Тест обязательных настроек"""
        self.assertTrue(hasattr(settings, "SECRET_KEY"))
        self.assertTrue(hasattr(settings, "DEBUG"))
        self.assertTrue(hasattr(settings, "ALLOWED_HOSTS"))
        self.assertTrue(hasattr(settings, "DATABASES"))
        self.assertTrue(hasattr(settings, "INSTALLED_APPS"))

    def test_rest_framework_settings(self):
        """Тест настроек REST Framework"""
        self.assertTrue(hasattr(settings, "REST_FRAMEWORK"))

        rf_settings = settings.REST_FRAMEWORK
        self.assertIn("DEFAULT_AUTHENTICATION_CLASSES", rf_settings)
        self.assertIn("DEFAULT_PERMISSION_CLASSES", rf_settings)

    def test_habit_validation_settings(self):
        """Тест настроек валидации привычек"""
        self.assertTrue(hasattr(settings, "HABIT_VALIDATION"))

        habit_settings = settings.HABIT_VALIDATION
        self.assertIn("MAX_DURATION_SECONDS", habit_settings)
        self.assertIn("MAX_BREAK_DAYS", habit_settings)
        self.assertIn("ALLOWED_FREQUENCIES", habit_settings)
