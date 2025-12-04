# Константы по умолчанию на случай, если настройки не заданы
DEFAULT_HABIT_VALIDATION = {
    "MAX_DURATION_SECONDS": 120,
    "MIN_FREQUENCY_DAYS": 1,
    "MAX_BREAK_DAYS": 7,
    "ALLOWED_FREQUENCIES": {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
    },
    "PLEASANT_HABIT_RULES": {
        "allow_reward": False,
        "allow_related_habit": False,
    },
    "USEFUL_HABIT_RULES": {
        "allow_only_one_of": ["reward", "related_habit"],
        "related_must_be_pleasant": True,
    },
}
