from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from habits.models import Habit

User = get_user_model()


class HabitPermissionsTestCase(TestCase):
    """Тесты для проверки прав доступа к привычкам"""

    def setUp(self):
        # Создаем тестовых пользователей
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        # Создаем тестовые привычки
        self.private_habit = Habit.objects.create(
            user=self.user1,
            place="Дом",
            time="08:00",
            action="Приватная привычка user1",
            duration=60,
            frequency="daily",
            is_public=False,
        )

        self.public_habit = Habit.objects.create(
            user=self.user1,
            place="Парк",
            time="09:00",
            action="Публичная привычка user1",
            duration=60,
            frequency="daily",
            is_public=True,
        )

        self.client = APIClient()

    def test_owner_can_crud_own_habits(self):
        """Владелец может выполнять CRUD операции со своими привычками"""
        self.client.force_authenticate(user=self.user1)

        # GET (чтение) своей приватной привычки
        response = self.client.get(f"/api/habits/{self.private_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PUT (обновление) своей привычки
        response = self.client.put(
            f"/api/habits/{self.private_habit.id}/",
            {"place": "Новое место", "time": "10:00", "action": "Обновлено", "duration": 60},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DELETE (удаление) своей привычки
        response = self.client.delete(f"/api/habits/{self.private_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_crud_other_private_habits(self):
        """Пользователь НЕ может выполнять CRUD с приватными привычками других"""
        self.client.force_authenticate(user=self.user2)

        # GET приватной привычки другого пользователя - 404 (не найдет в queryset)
        response = self.client.get(f"/api/habits/{self.private_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # PUT приватной привычки другого пользователя - 404
        response = self.client.put(f"/api/habits/{self.private_habit.id}/", {"place": "Пытаюсь изменить"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_view_public_habits_but_not_modify(self):
        """Пользователь может просматривать, но НЕ может изменять публичные привычки других"""
        self.client.force_authenticate(user=self.user2)

        # GET публичной привычки - разрешено
        response = self.client.get(f"/api/habits/{self.public_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PUT публичной привычки другого пользователя - запрещено
        response = self.client.put(f"/api/habits/{self.public_habit.id}/", {"place": "Пытаюсь изменить"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE публичной привычки - запрещено
        response = self.client.delete(f"/api/habits/{self.public_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_can_view_only_public_habits(self):
        """Неаутентифицированный пользователь может видеть только публичные привычки"""
        # GET публичной привычки - разрешено
        response = self.client.get(f"/api/habits/{self.public_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET приватной привычки - 404 (не найдет в queryset)
        response = self.client.get(f"/api/habits/{self.private_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # POST (создание) - требует аутентификации
        response = self.client.post(
            "/api/habits/", {"place": "Тест", "time": "10:00", "action": "Новая", "duration": 60}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_endpoint_shows_only_public_habits(self):
        """Эндпоинт /public/ показывает только публичные привычки"""
        # Для user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get("/api/habits/public/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру ответа
        self.assertIn("results", response.data)
        habits = response.data["results"]

        # Должна быть хотя бы одна публичная привычка
        self.assertGreater(len(habits), 0)

        # Проверяем первую привычку
        habit = habits[0]

        # Проверяем обязательные поля
        expected_fields = [
            "id",
            "user",
            "place",
            "time",
            "action",
            "frequency",
            "duration",
            "created_at",
            "full_description",
            "is_public",
        ]

        for field in expected_fields:
            self.assertIn(field, habit, f"Отсутствует поле {field}")

        # Проверяем что привычка публичная
        self.assertTrue(habit["is_public"])

        # Проверяем что full_description - строка
        self.assertIsInstance(habit["full_description"], str)

        # Проверяем что это наша тестовая публичная привычка
        self.assertEqual(habit["action"], "Публичная привычка user1")

    def test_my_habits_endpoint_shows_only_own_habits(self):
        """Эндпоинт /my_habits/ показывает только привычки текущего пользователя"""
        # Для user1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/habits/my_habits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        habits = response.data.get("results", []) if "results" in response.data else response.data
        for habit in habits:
            self.assertEqual(habit.get("user", {}).get("username"), "user1")

    def test_owner_can_update_own_habit(self):
        """Владелец может обновлять свою привычку"""
        self.client.force_authenticate(user=self.user1)

        data = {
            "place": "Обновленное место",
            "time": "10:00",
            "action": "Обновленное действие",
            "duration": 90,
            "frequency": "weekly",
            "is_public": True,
        }

        response = self.client.put(f"/api/habits/{self.private_habit.id}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.private_habit.refresh_from_db()
        self.assertEqual(self.private_habit.place, "Обновленное место")
        self.assertEqual(self.private_habit.action, "Обновленное действие")

    def test_other_user_cannot_update_public_habit(self):
        """Другой пользователь НЕ может обновлять публичную привычку"""
        self.client.force_authenticate(user=self.user2)

        data = {"action": "Пытаюсь изменить чужую привычку"}

        response = self.client.patch(f"/api/habits/{self.public_habit.id}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_habit(self):
        """Неаутентифицированный пользователь не может создать привычку"""
        data = {"place": "Тест", "time": "08:00", "action": "Новая привычка", "duration": 60}

        response = self.client.post("/api/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_create_habit(self):
        """Аутентифицированный пользователь может создать привычку"""
        self.client.force_authenticate(user=self.user2)

        data = {
            "place": "Новое место",
            "time": "09:00",
            "action": "Моя новая привычка",
            "duration": 60,
            "frequency": "daily",
            "is_public": False,
        }

        response = self.client.post("/api/habits/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем что привычка создана с правильным владельцем
        habit_id = response.data["id"]
        from habits.models import Habit

        habit = Habit.objects.get(id=habit_id)
        self.assertEqual(habit.user, self.user2)
        self.assertEqual(habit.action, "Моя новая привычка")
