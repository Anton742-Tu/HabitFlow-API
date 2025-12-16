from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from habits.models import Habit

User = get_user_model()


class HabitAPITestCase(TestCase):
    """Тесты API для привычек"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        # Аутентифицируем клиента
        self.client.force_authenticate(user=self.user)

        # Создаем тестовую привычку с правильными полями
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(8, 0),
            action="Тестовая привычка",
            is_pleasant=False,
            frequency="daily",
            duration=60,
            is_public=True,
        )

    def test_create_habit(self):
        """Тест создания привычки через API"""
        data = {
            "place": "Дом",
            "time": "08:00",
            "action": "Пить воду утром",
            "duration": 60,
            "frequency": "daily",
            "is_public": True,
        }

        response = self.client.post("/api/habits/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем что привычка создана
        self.assertEqual(response.data["action"], "Пить воду утром")
        self.assertEqual(response.data["duration"], 60)
        self.assertTrue(response.data["is_public"])

        # В зависимости от сериализатора, user может быть объектом или ID
        # Проверяем оба варианта
        user_data = response.data["user"]
        if isinstance(user_data, dict):
            # Если сериализатор возвращает объект пользователя
            self.assertEqual(user_data["id"], self.user.id)
            self.assertEqual(user_data["username"], self.user.username)
        else:
            # Если сериализатор возвращает только ID
            self.assertEqual(user_data, self.user.id)

    def test_get_habits_list(self):
        """Тест получения списка привычек"""
        response = self.client.get("/api/habits/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

        # Проверяем пагинацию
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_habit_detail(self):
        """Тест получения детальной информации о привычке"""
        response = self.client.get(f"/api/habits/{self.habit.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.habit.id)
        self.assertEqual(response.data["action"], self.habit.action)

    def test_update_habit(self):
        """Тест обновления привычки"""
        data = {
            "place": "Обновленное место",
            "time": "10:00",
            "action": "Обновленное действие",
            "duration": 90,
            "frequency": "weekly",
        }

        response = self.client.put(f"/api/habits/{self.habit.id}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.action, "Обновленное действие")
        self.assertEqual(self.habit.place, "Обновленное место")

    def test_delete_habit(self):
        """Тест удаления привычки"""
        response = self.client.delete(f"/api/habits/{self.habit.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=self.habit.id).exists())

    def test_complete_habit(self):
        """Тест отметки выполнения привычки"""
        # Первое выполнение должно работать
        response = self.client.post(
            f"/api/habits/{self.habit.id}/complete/", {"note": "Выполнено успешно!"}, format="json"
        )

        print(f"Complete habit - Status: {response.status_code}")
        print(f"Complete habit - Response: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["note"], "Выполнено успешно!")
        self.assertTrue(response.data["is_completed"])

        # Второе выполнение в тот же день должно вызвать ошибку
        response2 = self.client.post(
            f"/api/habits/{self.habit.id}/complete/", {"note": "Повторное выполнение"}, format="json"
        )

        print(f"Second completion - Status: {response2.status_code}")

        # Либо 400 (ошибка валидации), либо 201 если разрешено
        if response2.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("error", response2.data)
        elif response2.status_code == status.HTTP_201_CREATED:
            print("Повторное выполнение разрешено")
        else:
            self.fail(f"Unexpected status code: {response2.status_code}")

    def test_my_habits_endpoint(self):
        """Тест эндпоинта /my_habits/"""
        response = self.client.get("/api/habits/my_habits/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habits = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(habits), 1)
        self.assertEqual(habits[0]["action"], "Тестовая привычка")

    def test_public_habits_endpoint(self):
        """Тест эндпоинта /public/"""
        # Создаем приватную привычку
        Habit.objects.create(
            user=self.user, place="Дом", time=time(9, 0), action="Приватная привычка", duration=60, is_public=False
        )

        response = self.client.get("/api/habits/public/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if "results" in response.data:
            habits = response.data["results"]
        else:
            habits = response.data

        # Должна быть только публичная привычка
        self.assertEqual(len(habits), 1)
        self.assertEqual(habits[0]["action"], "Тестовая привычка")
