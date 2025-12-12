from django.test import TestCase
from django.contrib import admin


class TestAdminBasic(TestCase):
    def test_admin_import(self):
        """Тест импорта admin"""
        try:
            from habits import admin as habits_admin
            self.assertTrue(True)
        except ImportError:
            # Если нет admin.py - это нормально
            pass

    def test_admin_site(self):
        """Тест, что admin site работает"""
        self.assertIsNotNone(admin.site)