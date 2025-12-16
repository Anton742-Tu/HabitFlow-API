from django.conf import settings
from django.core.exceptions import ValidationError


def validate_duration(value):
    """Валидация времени выполнения"""
    max_duration = settings.HABIT_VALIDATION["MAX_DURATION_SECONDS"]

    if value > max_duration:
        raise ValidationError(f"Время выполнения должно быть не больше {max_duration} секунд.")
    if value <= 0:
        raise ValidationError("Время выполнения должно быть положительным числом.")


def validate_habit_consistency(habit):
    """Проверка согласованности полей привычки с настройками"""
    errors = []

    # Получаем настройки
    pleasant_rules = settings.HABIT_VALIDATION["PLEASANT_HABIT_RULES"]
    useful_rules = settings.HABIT_VALIDATION["USEFUL_HABIT_RULES"]

    if habit.is_pleasant:
        # Правила для приятных привычек
        if not pleasant_rules["allow_reward"] and habit.reward:
            errors.append("У приятной привычки не может быть вознаграждения.")

        if not pleasant_rules["allow_related_habit"] and habit.related_habit:
            errors.append("У приятной привычки не может быть связанной привычки.")
    else:
        # Правила для полезных привычек
        # Проверяем, что указано только одно: либо вознаграждение, либо связанная привычка
        has_reward = bool(habit.reward and habit.reward.strip())
        has_related = habit.related_habit is not None

        if has_reward and has_related:
            errors.append("Нельзя одновременно указывать и связанную привычку и вознаграждение.")

        # Проверяем, что связанная привычка приятная
        if has_related and useful_rules["related_must_be_pleasant"]:
            if not habit.related_habit.is_pleasant:
                errors.append("Связанная привычка должна быть приятной привычкой.")

    if errors:
        raise ValidationError(errors)


def validate_completion_frequency(habit, completion_date):
    """Проверка периодичности выполнения"""
    max_break_days = settings.HABIT_VALIDATION["MAX_BREAK_DAYS"]

    if not habit.completions.exists():
        return

    last_completion = habit.completions.latest("completed_at")
    days_since_last = (completion_date - last_completion.completed_at).days

    if days_since_last > max_break_days:
        raise ValidationError(
            f"Привычка не выполнялась {days_since_last} дней. " f"Максимальный перерыв - {max_break_days} дней."
        )


def validate_frequency_choice(frequency):
    """Валидация выбора периодичности"""
    allowed_frequencies = settings.HABIT_VALIDATION["ALLOWED_FREQUENCIES"]

    if frequency not in allowed_frequencies:
        raise ValidationError(
            f'Недопустимая периодичность. Допустимые значения: {", ".join(allowed_frequencies.keys())}'
        )


def validate_too_frequent_completion(habit, completion_date):
    """Проверка, что привычка не выполняется слишком часто"""
    if not habit.completions.exists():
        return

    # Получаем минимальный интервал из настроек
    min_interval_days = settings.HABIT_VALIDATION["MIN_FREQUENCY_DAYS"]

    last_completion = habit.completions.latest("completed_at")
    days_since_last = (completion_date - last_completion.completed_at).days

    if days_since_last < min_interval_days:
        raise ValidationError(
            f"Привычку можно выполнять раз в {min_interval_days} дней. " f"Прошло только {days_since_last} дней."
        )
