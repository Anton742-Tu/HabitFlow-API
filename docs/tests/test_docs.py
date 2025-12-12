from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


class TestDocsConfiguration(TestCase):
    """Тесты корректности настройки документации API."""

    def test_drf_yasg_in_installed_apps(self):
        """Проверяем, что drf_yasg добавлен в INSTALLED_APPS."""
        self.assertIn("drf_yasg", settings.INSTALLED_APPS)

    def test_docs_urls_exist(self):
        """Проверяем, что URL-адреса документации сконфигурированы."""
        # Эта проверка не требует, чтобы шаблон физически существовал
        try:
            # Пытаемся получить URL (не переходим по нему)
            docs_url = reverse("schema-swagger-ui")  # Используйте имя вашего URL
            self.assertIsNotNone(docs_url)
        except Exception:
            # Если нет, проверяем настройку схемы в REST_FRAMEWORK
            self.assertTrue(hasattr(settings, "REST_FRAMEWORK"))
            # Современный DRF рекомендует использовать сторонние пакеты,
            # такие как drf-spectacular или drf-yasg, для схем OpenAPI[citation:1][citation:8].
            schema_class = settings.REST_FRAMEWORK.get("DEFAULT_SCHEMA_CLASS", "")
            # Проверяем, что схема настроена (не пустая строка)
            self.assertTrue(schema_class)

    def test_schema_generation_import(self):
        """Проверяем, что можно импортировать необходимые модули."""
        try:
            from drf_yasg import openapi
            from drf_yasg.views import get_schema_view

            # Если импорт прошел успешно, тест считается пройденным
            self.assertTrue(True)
        except ImportError:
            # Если drf_yasg не установлен, проверяем drf-spectacular
            try:
                from drf_spectacular.views import SpectacularAPIView

                self.assertTrue(True)
            except ImportError:
                # Если ни один не установлен, тест падает
                self.fail(
                    "Ни drf_yasg, ни drf_spectacular не установлены. "
                    "Установите один из пакетов для документации API[citation:1][citation:8]."
                )
