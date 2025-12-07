import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    """Модель для связи пользователя Django с Telegram"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_profile",
        verbose_name="Пользователь",
    )
    chat_id = models.BigIntegerField(unique=True, verbose_name="ID чата в Telegram")
    telegram_username = models.CharField(max_length=255, blank=True, verbose_name="Имя пользователя в Telegram")
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    language_code = models.CharField(max_length=10, default="ru")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} (@{self.telegram_username})"


class NotificationSettings(models.Model):
    """Настройки уведомлений для пользователя"""

    telegram_user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE, related_name="notification_settings")

    # Время уведомлений
    morning_reminder_time = models.TimeField(default="09:00", verbose_name="Утреннее напоминание")
    evening_reminder_time = models.TimeField(default="21:00", verbose_name="Вечернее напоминание")

    # Типы уведомлений
    enable_daily_reminders = models.BooleanField(default=True, verbose_name="Ежедневные напоминания")
    enable_habit_reminders = models.BooleanField(default=True, verbose_name="Напоминания о привычках")
    enable_weekly_reports = models.BooleanField(default=True, verbose_name="Еженедельные отчеты")
    enable_streak_alerts = models.BooleanField(default=True, verbose_name="Оповещения о сериях")

    # Настройки времени
    remind_before_minutes = models.PositiveIntegerField(default=15, verbose_name="Напоминать за (минут)")
    timezone = models.CharField(max_length=50, default="Europe/Moscow", verbose_name="Часовой пояс")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройка уведомлений"
        verbose_name_plural = "Настройки уведомлений"

    def __str__(self):
        return f"Настройки для {self.telegram_user.user.username}"


class SentNotification(models.Model):
    """История отправленных уведомлений"""

    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="sent_notifications")
    habit = models.ForeignKey("habits.Habit", on_delete=models.CASCADE, null=True, blank=True)
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
    """Код для подключения Telegram аккаунта"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="telegram_connection_codes"
    )
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Код подключения Telegram"
        verbose_name_plural = "Коды подключения Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.code}"

    def is_valid(self):
        """Проверка что код еще действителен"""
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_code(cls, user):
        """Генерация нового кода для пользователя"""
        # Деактивируем старые коды пользователя
        cls.objects.filter(user=user, is_used=False).update(is_used=True)

        # Генерируем новый код
        code = secrets.token_urlsafe(8)

        # Создаем запись
        connection_code = cls.objects.create(user=user, code=code, expires_at=timezone.now() + timedelta(minutes=10))

        return connection_code

    def mark_as_used(self):
        """Пометить код как использованный"""
        self.is_used = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # По умолчанию код действителен 10 минут
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
