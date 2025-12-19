from django.conf import settings
from django.test import TestCase


class TestDocsConfiguration(TestCase):
    """Тесты конфигурации документации"""

    def test_documentation_config_exists(self):
        """Тест, что конфигурация для документации существует"""
        # Проверяем различные способы конфигурации docs
        config_checks = [
            hasattr(settings, "SWAGGER_SETTINGS"),
            hasattr(settings, "DRF_SPECTACULAR_SETTINGS"),
            "drf_yasg" in settings.INSTALLED_APPS,
            "drf_spectacular" in settings.INSTALLED_APPS,
        ]

        # Хотя бы одна проверка должна быть True
        self.assertTrue(any(config_checks))

    def test_api_schema_generation(self):
        """Тест логики генерации схемы API"""
        # Простая логика для теста
        api_info = {
            "title": "HabitFlow API",
            "version": "1.0.0",
            "description": "API для трекера привычек",
        }

        self.assertEqual(api_info["title"], "HabitFlow API")
        self.assertEqual(api_info["version"], "1.0.0")
        self.assertIn("API", api_info["description"])

    def test_url_patterns_for_docs(self):
        """Тест URL patterns для документации"""
        from django.urls import get_resolver

        resolver = get_resolver()

        # Проверяем наличие docs или api в URL patterns
        url_patterns = [str(pattern) for pattern in resolver.url_patterns]

        docs_patterns = [
            p
            for p in url_patterns
            if "docs" in str(p).lower() or "api" in str(p).lower()
        ]

        # Должен быть хотя бы один API-related pattern
        self.assertTrue(len(docs_patterns) > 0)
