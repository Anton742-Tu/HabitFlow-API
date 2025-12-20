from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .validators import (
    validate_completion_frequency,
    validate_duration,
    validate_frequency_choice,
    validate_habit_consistency,
    validate_too_frequent_completion,
)


class Habit(models.Model):
    """Модель привычки"""

    # Периодичность выполнения (берем ключи из настроек)
    FREQUENCY_CHOICES = [
        (key, key.capitalize())
        for key in settings.HABIT_VALIDATION["ALLOWED_FREQUENCIES"].keys()
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )

    place = models.CharField(
        max_length=255,
        verbose_name="Место выполнения",
        help_text="Место, в котором необходимо выполнять привычку",
    )

    time = models.TimeField(
        verbose_name="Время выполнения",
        help_text="Время, когда необходимо выполнять привычку",
    )

    action = models.CharField(
        max_length=500,
        verbose_name="Действие",
        help_text='Конкретное действие, например: "пробежать 1 км"',
    )

    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Приятная привычка",
        help_text="Является ли привычка приятной (вознаграждением)",
    )

    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_habits",
        verbose_name="Связанная привычка",
        help_text="Полезная привычка, связанная с этой приятной привычкой",
    )

    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
        help_text="Чем пользователь должен себя вознаградить после выполнения",
    )

    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default="daily",
        verbose_name="Периодичность",
        help_text="Как часто выполнять привычку",
    )

    duration = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(1), validate_duration],
        verbose_name="Время на выполнение (в секундах)",
        help_text="Время на выполнение должно быть не более 120 секунд",
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичная привычка",
        help_text="Могут ли другие пользователи видеть эту привычку",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["time"]
        constraints = [
            models.CheckConstraint(
                name="duration_max_120_seconds",
                check=models.Q(
                    duration__lte=settings.HABIT_VALIDATION["MAX_DURATION_SECONDS"]
                ),
            ),
            # Ограничение: у приятной привычки не может быть вознаграждения
            models.CheckConstraint(
                name="pleasant_no_reward",
                check=~(models.Q(is_pleasant=True) & models.Q(reward__gt="")),
            ),
            # Ограничение: у приятной привычки не может быть связанной привычки
            models.CheckConstraint(
                name="pleasant_no_related",
                check=~(
                    models.Q(is_pleasant=True) & models.Q(related_habit__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.action} в {self.time}"

    def clean(self):
        """Валидация модели перед сохранением"""
        # Проверяем согласованность полей
        validate_habit_consistency(self)

        # Проверяем выбор периодичности
        validate_frequency_choice(self.frequency)

        super().clean()

    @property
    def frequency_days(self):
        """Возвращает периодичность в днях из настроек"""
        return settings.HABIT_VALIDATION["ALLOWED_FREQUENCIES"].get(self.frequency, 1)

    def can_be_completed_today(self):
        # Получаем frequency_days как число
        if hasattr(self, "frequency_days"):
            # Если это свойство, используем его
            frequency = self.frequency_days
        else:
            # Конвертируем frequency в дни
            frequency_map = {
                "daily": 1,
                "weekly": 7,
                "monthly": 30,
            }
            frequency = frequency_map.get(self.frequency, 1)

        # Получаем days_since_last как число
        days_since_last = self.days_since_last_completion() or 0

        # Сравниваем числа
        return int(days_since_last) >= int(frequency)

    @property
    def full_description(self):
        """Генерация полного описания привычки в формате из книги"""
        try:
            time_str = self.time.strftime("%H:%M") if self.time else "??:??"
            return f"Я буду {self.action.lower()} в {time_str} в {self.place}"
        except AttributeError:
            # Если каких-то атрибутов нет (например, в тестах)
            return (
                f"Я буду {getattr(self, 'action', 'действие')} в {getattr(self, 'time', 'время')}/n"
                f"в {getattr(self, 'place', 'место')}"
            )


class HabitCompletion(models.Model):
    """Модель для отслеживания выполнения привычек"""

    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="completions",
        verbose_name="Привычка",
    )

    completed_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время выполнения"
    )

    is_completed = models.BooleanField(default=True, verbose_name="Выполнено")

    note = models.TextField(
        blank=True,
        verbose_name="Заметка",
        help_text="Необязательная заметка о выполнении",
    )

    class Meta:
        verbose_name = "Выполнение привычки"
        verbose_name_plural = "Выполнения привычек"
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["habit", "completed_at"]),
        ]
        constraints = [
            # Ограничение: нельзя выполнять привычку реже, чем 1 раз в 7 дней
            # (проверяется в save методе, но можно добавить constraint если нужно)
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.habit.action} — {self.completed_at.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Валидация выполнения привычки"""
        if not self.pk:  # Только при создании нового выполнения
            # Проверяем, что привычка не выполняется слишком редко
            validate_completion_frequency(self.habit, self.completed_at)

            # Проверяем, что привычка не выполняется слишком часто
            validate_too_frequent_completion(self.habit, self.completed_at)

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для проверки периодичности"""
        if not self.pk:  # Только при создании нового выполнения
            # Проверяем, можно ли выполнять привычку по периодичности
            if not self.habit.can_be_completed_today():
                min_interval = self.habit.frequency_days
                last_completion = self.habit.completions.latest("completed_at")
                days_since_last = (timezone.now() - last_completion.completed_at).days

                raise ValidationError(
                    f"Привычку можно выполнять раз в {min_interval} дней. "
                    f"Прошло только {days_since_last} дней."
                )

        self.full_clean()
        super().save(*args, **kwargs)
