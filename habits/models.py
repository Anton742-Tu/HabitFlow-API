from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .validators import validate_completion_frequency, validate_duration, validate_habit_consistency


class Habit(models.Model):
    """Модель привычки"""

    # Периодичность выполнения
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    PERIOD_CHOICES = [
        (DAILY, "Ежедневно"),
        (WEEKLY, "Еженедельно"),
        (MONTHLY, "Ежемесячно"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habits", verbose_name="Пользователь"
    )

    place = models.CharField(
        max_length=255, verbose_name="Место выполнения", help_text="Место, в котором необходимо выполнять привычку"
    )

    time = models.TimeField(verbose_name="Время выполнения", help_text="Время, когда необходимо выполнять привычку")

    action = models.CharField(
        max_length=500, verbose_name="Действие", help_text='Конкретное действие, например: "пробежать 1 км"'
    )

    is_pleasant = models.BooleanField(
        default=False, verbose_name="Приятная привычка", help_text="Является ли привычка приятной (вознаграждением)"
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

    frequency = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default=DAILY,
        verbose_name="Периодичность",
        help_text="Как часто выполнять привычку",
    )

    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
        help_text="Чем пользователь должен себя вознаградить после выполнения",
    )

    duration = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(1), validate_duration],
        verbose_name="Время на выполнение (в секундах)",
        help_text="Время на выполнение должно быть не более 120 секунд",
    )

    is_public = models.BooleanField(
        default=False, verbose_name="Публичная привычка", help_text="Могут ли другие пользователи видеть эту привычку"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["time"]
        constraints = [
            models.CheckConstraint(name="duration_max_120_seconds", condition=models.Q(duration__lte=120)),
            # Ограничение: нельзя одновременно указывать и связанную привычку и вознаграждение
            models.CheckConstraint(
                name="exclusive_reward_or_related",
                condition=~(models.Q(related_habit__isnull=False) & models.Q(reward__gt="")),
            ),
            # Ограничение: у приятной привычки не может быть вознаграждения
            models.CheckConstraint(
                name="pleasant_no_reward", condition=~(models.Q(is_pleasant=True) & models.Q(reward__gt=""))
            ),
            # Ограничение: у приятной привычки не может быть связанной привычки
            models.CheckConstraint(
                name="pleasant_no_related",
                condition=~(models.Q(is_pleasant=True) & models.Q(related_habit__isnull=False)),
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.action} в {self.time}"

    def clean(self):
        """Валидация модели перед сохранением"""
        # Проверяем согласованность полей
        validate_habit_consistency(self)

        # Проверяем, что связанная привычка приятная
        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной привычкой.")

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической валидации"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def full_description(self):
        """Генерация полного описания привычки в формате из книги"""
        return f"Я буду {self.action.lower()} в {self.time.strftime('%H:%M')} в {self.place}"

    @property
    def frequency_days(self):
        """Возвращает периодичность в днях"""
        frequency_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
        }
        return frequency_map.get(self.frequency, 1)

    def can_be_completed_today(self):
        """Можно ли выполнить привычку сегодня (проверка по периодичности)"""
        if not self.completions.exists():
            return True

        last_completion = self.completions.latest("completed_at")
        days_since_last = (timezone.now() - last_completion.completed_at).days

        return days_since_last >= self.frequency_days


class HabitCompletion(models.Model):
    """Модель для отслеживания выполнения привычек"""

    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="completions", verbose_name="Привычка")

    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время выполнения")

    is_completed = models.BooleanField(default=True, verbose_name="Выполнено")

    note = models.TextField(blank=True, verbose_name="Заметка", help_text="Необязательная заметка о выполнении")

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
        # Проверяем, что привычка не выполняется слишком редко
        validate_completion_frequency(self.habit, self.completed_at)

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для проверки периодичности"""
        if not self.pk:  # Только при создании нового выполнения
            # Проверяем, можно ли выполнять привычку по периодичности
            if not self.habit.can_be_completed_today():
                raise ValidationError(
                    f"Привычку можно выполнять раз в {self.habit.frequency_days} дней. " f"Слишком часто!"
                )

        self.full_clean()
        super().save(*args, **kwargs)
