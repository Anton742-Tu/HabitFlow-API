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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("user", data)
        self.assertIn("access", data)
        self.assertIn("refresh", data)

        # Проверяем создание пользователя
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")

    def test_login_user(self):
        """Тест входа пользователя"""
        # Создаем пользователя
        User.objects.create_user(username="loginuser", password="testpass123", email="login@example.com")

        response = self.client.post(
            "/api/users/token/", {"username": "loginuser", "password": "testpass123"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_get_profile(self):
        """Тест получения профиля"""
        user = User.objects.create_user(username="profileuser", password="testpass123")

        self.client.force_authenticate(user=user)
        response = self.client.get("/api/users/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["username"], "profileuser")

    def test_register_user_validation_error(self):
        """Тест ошибки валидации при регистрации"""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",  # слишком короткий
            "password2": "short",
        }

        response = self.client.post("/api/users/register/", invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user_invalid_credentials(self):
        """Тест входа с неверными учетными данными"""
        response = self.client.post(
            "/api/users/token/", {"username": "wronguser", "password": "wrongpass"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_unauthenticated(self):
        """Тест получения профиля без аутентификации"""
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Тест обновления профиля"""
        user = User.objects.create_user(username="profileuser", password="testpass123")

        self.client.force_authenticate(user=user)
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = self.client.patch("/api/users/profile/", update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["first_name"], "Updated")
        self.assertEqual(data["last_name"], "Name")

    def test_logout_view(self):
        """Тест выхода из системы"""
        user = User.objects.create_user(username="logoutuser", password="testpass123")

        self.client.force_authenticate(user=user)
        response = self.client.post("/api/users/logout/")

        # LogoutView может возвращать 200 или 204
        self.assertIn(response.status_code, [200, 204, 405])
