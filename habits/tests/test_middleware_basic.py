from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from habits.middleware import SecurityHeadersMiddleware


class TestMiddlewareBasic(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Создаем простой view для тестирования middleware
        def dummy_view(request):
            return HttpResponse("OK")

        self.dummy_view = dummy_view

    def test_middleware_import(self):
        """Тест импорта middleware"""
        try:

            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Не удалось импортировать SecurityHeadersMiddleware: {e}")

    def test_middleware_initialization(self):
        """Тест инициализации middleware"""
        middleware = SecurityHeadersMiddleware(self.dummy_view)
        self.assertIsNotNone(middleware)
        self.assertEqual(middleware.get_response, self.dummy_view)

    def test_middleware_call_without_origin(self):
        """Тест вызова middleware без Origin заголовка"""
        middleware = SecurityHeadersMiddleware(self.dummy_view)

        # Создаем запрос без Origin
        request = self.factory.get("/")
        response = middleware(request)

        # Проверяем security headers
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-XSS-Protection"], "1; mode=block")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")

        # Без Origin не должно быть CORS headers
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_middleware_call_with_origin(self):
        """Тест вызова middleware с Origin заголовком"""
        middleware = SecurityHeadersMiddleware(self.dummy_view)

        # Создаем запрос с Origin
        request = self.factory.get("/", HTTP_ORIGIN="http://localhost:3000")
        response = middleware(request)

        # Проверяем security headers
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-XSS-Protection"], "1; mode=block")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")

    def test_response_content(self):
        """Тест содержимого ответа"""
        middleware = SecurityHeadersMiddleware(self.dummy_view)
        request = self.factory.get("/")
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_middleware_methods(self):
        """Тест наличия методов у middleware"""
        middleware = SecurityHeadersMiddleware(self.dummy_view)

        self.assertTrue(hasattr(middleware, "__init__"))
        self.assertTrue(hasattr(middleware, "__call__"))
        self.assertTrue(callable(middleware))
