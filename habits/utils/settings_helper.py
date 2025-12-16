from django.conf import settings

from .constants import DEFAULT_HABIT_VALIDATION


def get_habit_settings():
    """Безопасное получение настроек привычек"""
    return getattr(settings, "HABIT_VALIDATION", DEFAULT_HABIT_VALIDATION)
