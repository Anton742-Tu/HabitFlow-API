from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_duration(value):
    """Валидация времени выполнения (не более 120 секунд)"""
    if value > 120:
        raise ValidationError("Время выполнения должно быть не больше 120 секунд.")
    if value <= 0:
        raise ValidationError("Время выполнения должно быть положительным числом.")


def validate_frequency(frequency, created_at):
    """Валидация периодичности выполнения (не реже 1 раза в 7 дней)"""
    # Здесь логика будет дополнена после создания модели выполнения привычек
    pass


def validate_completion_frequency(habit, completion_date):
    """Проверка, что привычка выполняется не реже чем раз в 7 дней"""
    if not habit.completions.exists():
        return

    last_completion = habit.completions.latest("completed_at")
    days_since_last = (completion_date - last_completion.completed_at).days

    if days_since_last > 7:
        raise ValidationError(f"Привычка не выполнялась {days_since_last} дней. " f"Максимальный перерыв - 7 дней.")


def validate_habit_consistency(habit):
    """Проверка согласованности полей привычки"""
    errors = []

    # 1. Исключить одновременный выбор связанной привычки и указания вознаграждения
    if habit.related_habit and habit.reward:
        errors.append("Нельзя одновременно указывать и связанную привычку и вознаграждение.")

    # 2. В связанные привычки могут попадать только привычки с признаком приятной привычки
    if habit.related_habit and not habit.related_habit.is_pleasant:
        errors.append("Связанная привычка должна быть приятной привычкой.")

    # 3. У приятной привычки не может быть вознаграждения или связанной привычки
    if habit.is_pleasant:
        if habit.reward:
            errors.append("У приятной привычки не может быть вознаграждения.")
        if habit.related_habit:
            errors.append("У приятной привычки не может быть связанной привычки.")

    # 4. Приятная привычка не может иметь ни вознаграждения, ни связанной привычки
    if habit.is_pleasant and (habit.reward or habit.related_habit):
        errors.append("Приятная привычка не должна иметь вознаграждения или связанных привычек.")

    if errors:
        raise ValidationError(errors)


def validate_habit_timing(habit):
    """Проверка временных ограничений привычки"""
    # Проверяем, что привычка не планируется на прошедшее время (опционально)
    from datetime import datetime
    from datetime import time as datetime_time

    # Если хотим проверять, что время не в прошлом
    # current_time = timezone.now().time()
    # if habit.time < current_time:
    #     raise ValidationError('Время выполнения привычки не должно быть в прошлом.')
    pass
