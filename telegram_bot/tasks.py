import logging

from django.utils import timezone

from habits.models import Habit

from .models import TelegramUser
from .services import TelegramBotService

logger = logging.getLogger(__name__)


def send_scheduled_reminders():
    """Отправка напоминаний по расписанию"""
    logger.info(f"Запуск отправки напоминаний в {timezone.now()}")

    bot_service = TelegramBotService()
    now = timezone.now()
    current_time = now.time()

    # Находим привычки, которые нужно выполнить сейчас
    # (в реальности здесь сложная логика с учетом часовых поясов)
    habits = Habit.objects.filter(
        is_active=True  # Добавьте это поле в модель Habit или уберите фильтр
    ).select_related("user")

    reminders_sent = 0

    for habit in habits:
        try:
            # Проверяем время привычки (±15 минут)
            habit_time = habit.time
            if not habit_time:
                continue

            time_diff = abs(
                (current_time.hour * 60 + current_time.minute)
                - (habit_time.hour * 60 + habit_time.minute)
            )

            if time_diff <= 15:  # В пределах 15 минут
                # Проверяем, подключен ли пользователь к Telegram
                try:
                    telegram_user = TelegramUser.objects.get(
                        user=habit.user, is_active=True
                    )

                    # Отправляем напоминание
                    bot_service.send_habit_reminder(
                        chat_id=telegram_user.chat_id, habit=habit
                    )

                    reminders_sent += 1
                    logger.info(
                        f"Отправлено напоминание для {habit.user.username}: {habit.action}"
                    )

                except TelegramUser.DoesNotExist:
                    continue
                except Exception as e:
                    logger.error(
                        f"Ошибка отправки напоминания для привычки {habit.id}: {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Ошибка обработки привычки {habit.id}: {e}")

    logger.info(f"Отправлено {reminders_sent} напоминаний")
    return reminders_sent
