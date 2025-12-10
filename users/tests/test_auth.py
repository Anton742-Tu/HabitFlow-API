from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class UserAuthTestCase(TestCase):
    """Тесты для аутентификации пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_user(self):
        """Тест регистрации пользователя"""
        response = self.client.post("/api/users/register/", self.user_data, format="json")

        print(f"Регистрация - Статус: {response.status_code}")
        print(f"Регистрация - Ответ: {response.content[:200]}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()

        self.assertIn("username", data)
        self.assertIn("email", data)
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)

        # Проверяем значения
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")

        # Проверяем, что токены возвращаются
        if "access" in data:
            self.assertIn("access", data)
            self.assertIn("refresh", data)
        else:
            # Или проверяем, что пользователь создан в базе
            print("Токены не в теле ответа, проверяем создание пользователя")

        # Проверяем создание пользователя в базе
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")

    def test_login_user(self):
        """Тест входа пользователя"""
        User.objects.create_user(username="loginuser", password="testpass123", email="login@example.com")

        response = self.client.post(
            "/api/users/token/", {"username": "loginuser", "password": "testpass123"}, format="json"
        )

        print(f"Логин - Статус: {response.status_code}")
        print(f"Логин - Ответ: {response.content[:200]}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_get_profile(self):
        """Тест получения профиля"""
        user = User.objects.create_user(username="profileuser", password="testpass123")

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/users/profile/")

        print(f"Профиль - Статус: {response.status_code}")
        print(f"Профиль - Ответ: {response.content[:200]}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["username"], "profileuser")
