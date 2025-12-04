from django.core.exceptions import ValidationError


def validate_habit_duration(value):
    """Валидация времени выполнения привычки"""
    if value > 120:
        raise ValidationError(
            'Время выполнения привычки не должно превышать 120 секунд'
        )
