import os
import sys
from pathlib import Path

import django
from django.contrib.auth import get_user_model
from django.test import TestCase

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_config")

# Инициализируем Django
django.setup()


User = get_user_model()


class SimpleWorkingTest(TestCase):
    """Простой тест который точно работает"""

    def test_create_user(self):
        """Тест создания пользователя"""
        print("1. Создаем пользователя...")
        user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        print(f"   ✅ Пользователь создан: {user.username}")

    def test_user_count(self):
        """Тест подсчета пользователей"""
        print("2. Считаем пользователей...")

        # Создаем несколько пользователей
        User.objects.create_user("user1", "user1@test.com", "pass1")
        User.objects.create_user("user2", "user2@test.com", "pass2")

        count = User.objects.count()
        print(f"   ✅ Пользователей в базе: {count}")
        self.assertGreaterEqual(count, 2)

    def test_simple_assertion(self):
        """Простой тест утверждения"""
        print("3. Простой тест утверждения...")
        self.assertEqual(1 + 1, 2)
        print("   ✅ 1 + 1 = 2 ✓")


if __name__ == "__main__":
    import unittest

    print("=" * 50)
    print("Запуск простого теста")
    print("=" * 50)

    # Запускаем тесты
    suite = unittest.TestLoader().loadTestsFromTestCase(SimpleWorkingTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("❌ ЕСТЬ ОШИБКИ")
    print("=" * 50)

    sys.exit(0 if result.wasSuccessful() else 1)
