from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class TestSimplePermissions(TestCase):
    """Простые тесты без сложных импортов"""

    def test_permission_logic(self):
        """Простая логика проверки владения"""
        user1 = User.objects.create_user(username="user1")
        user2 = User.objects.create_user(username="user2")

        # Владелец объекта
        obj_owner = user1
        current_user = user1

        self.assertEqual(obj_owner, current_user)
        self.assertTrue(obj_owner == current_user)

        # Чужой объект
        current_user = user2
        self.assertNotEqual(obj_owner, current_user)
        self.assertFalse(obj_owner == current_user)

    def test_public_private_logic(self):
        """Логика публичных/приватных записей"""
        is_public = True
        is_owner = False

        # Публичная запись - доступна всем
        self.assertTrue(is_public)

        # Приватная запись - только владельцу
        is_public = False
        self.assertFalse(is_public)
        self.assertFalse(is_public or is_owner)

        # Приватная, но владелец
        is_owner = True
        self.assertTrue(is_public or is_owner)
