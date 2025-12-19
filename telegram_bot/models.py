from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class TelegramUser(models.Model):
    """Пользователь Telegram, связанный с Django User"""

    django_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_user",
        verbose_name="Пользователь Django",
    )

    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID в Telegram",
        help_text="Числовой ID пользователя в Telegram",
    )

    username = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Username в Telegram"
    )

    first_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Имя в Telegram"
    )

    last_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Фамилия в Telegram"
    )

    is_active = models.BooleanField(
        default=True, verbose_name="Бот активен для пользователя"
    )

    language_code = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Код языка"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.django_user.username} ({self.telegram_id})"


class NotificationSettings(models.Model):
    """Настройки уведомлений для пользователя"""

    telegram_user = models.OneToOneField(
        TelegramUser, on_delete=models.CASCADE, related_name="notification_settings"
    )

    # Время уведомлений
    morning_reminder_time = models.TimeField(
        default="09:00", verbose_name="Утреннее напоминание"
    )
    evening_reminder_time = models.TimeField(
        default="21:00", verbose_name="Вечернее напоминание"
    )

    # Типы уведомлений
    enable_daily_reminders = models.BooleanField(
        default=True, verbose_name="Ежедневные напоминания"
    )
    enable_habit_reminders = models.BooleanField(
        default=True, verbose_name="Напоминания о привычках"
    )
    enable_weekly_reports = models.BooleanField(
        default=True, verbose_name="Еженедельные отчеты"
    )
    enable_streak_alerts = models.BooleanField(
        default=True, verbose_name="Оповещения о сериях"
    )

    # Настройки времени
    remind_before_minutes = models.PositiveIntegerField(
        default=15, verbose_name="Напоминать за (минут)"
    )
    timezone = models.CharField(
        max_length=50, default="Europe/Moscow", verbose_name="Часовой пояс"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройка уведомлений"
        verbose_name_plural = "Настройки уведомлений"

    def __str__(self):
        return f"Настройки для {self.telegram_user.user.username}"


class SentNotification(models.Model):
    """История отправленных уведомлений"""

    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    habit = models.ForeignKey(
        "habits.Habit", on_delete=models.CASCADE, null=True, blank=True
    )
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ("habit_reminder", "Напоминание о привычке"),
            ("daily_summary", "Ежедневный отчет"),
            ("weekly_report", "Еженедельный отчет"),
            ("streak_alert", "Оповещение о серии"),
            ("welcome", "Приветственное сообщение"),
        ],
    )
    message_text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Отправленное уведомление"
        verbose_name_plural = "Отправленные уведомления"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["sent_at", "notification_type"]),
        ]

    def __str__(self):
        return f"{self.notification_type} для {self.telegram_user.user.username}"


class TelegramConnectionCode(models.Model):
    """Код для привязки Telegram аккаунта"""

    django_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_codes",
        verbose_name="Пользователь Django",
    )

    code = models.CharField(max_length=6, unique=True, verbose_name="Код подтверждения")

    telegram_id = models.BigIntegerField(
        null=True, blank=True, verbose_name="ID в Telegram (после привязки)"
    )

    is_used = models.BooleanField(default=False, verbose_name="Использован")

    expires_at = models.DateTimeField(verbose_name="Действителен до")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Код привязки Telegram"
        verbose_name_plural = "Коды привязки Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Код {self.code} для {self.django_user.username}"

    def save(self, *args, **kwargs):
        if not self.code:
            # Генерируем случайный 6-значный код
            self.code = get_random_string(6, "0123456789")
        if not self.expires_at:
            # Код действует 10 минут
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_code(cls, user):
        """Генерация уникального кода для подключения Telegram"""
        import uuid

        code = uuid.uuid4().hex[:6].upper()

        # Удаляем старые коды пользователя - используем правильное имя поля
        cls.objects.filter(django_user=user, is_used=False).delete()  # ← ИЗМЕНЕНО

        # Создаем новый код
        connection_code = cls.objects.create(
            django_user=user,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),  # ← ИЗМЕНЕНО
        )
        return connection_code
