import logging

from celery import shared_task
from django.utils import timezone

from habits.models import Habit
from telegram_bot.models import TelegramUser
from telegram_bot.services import TelegramBotService

logger = logging.getLogger(__name__)


@shared_task
def send_habit_reminders():
    """Отправка напоминаний о привычках"""
    now = timezone.now()
    current_time = now.time()

    # Находим привычки, которые нужно выполнить в ближайшие 5 минут
    habits = Habit.objects.filter(is_active=True).select_related(
        "user"
    )  # Предполагаем, что добавили это поле

    bot_service = TelegramBotService()
    notifications_sent = 0

    for habit in habits:
        try:
            # Проверяем время привычки (±5 минут)
            habit_time = habit.time
            time_diff = abs(
                (current_time.hour * 60 + current_time.minute)
                - (habit_time.hour * 60 + habit_time.minute)
            )

            if time_diff <= 5:  # В пределах 5 минут
                # Проверяем, подключен ли пользователь к Telegram
                try:
                    telegram_user = TelegramUser.objects.get(
                        user=habit.user, is_active=True
                    )
                    settings = telegram_user.notification_settings

                    if settings.enable_habit_reminders:
                        # Проверяем, не было ли уже напоминания сегодня
                        from telegram_bot.models import SentNotification

                        today_start = now.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )

                        already_sent = SentNotification.objects.filter(
                            telegram_user=telegram_user,
                            habit=habit,
                            notification_type="habit_reminder",
                            sent_at__gte=today_start,
                        ).exists()

                        if not already_sent:
                            bot_service.send_habit_reminder(
                                chat_id=telegram_user.chat_id, habit=habit
                            )

                            # Сохраняем в историю
                            SentNotification.objects.create(
                                telegram_user=telegram_user,
                                habit=habit,
                                notification_type="habit_reminder",
                                message_text=f"Напоминание: {habit.action}",
                                is_delivered=True,
                            )

                            notifications_sent += 1

                except TelegramUser.DoesNotExist:
                    continue
                except Exception as e:
                    logger.error(f"Error sending reminder for habit {habit.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing habit {habit.id}: {e}")

    return f"Sent {notifications_sent} habit reminders"


@shared_task
def send_daily_summaries():
    """Отправка ежедневных отчетов"""
    now = timezone.now()
    current_time = now.time()

    # Отправляем в 21:00
    if current_time.hour == 21 and current_time.minute == 0:
        bot_service = TelegramBotService()

        # Находим всех пользователей с активными Telegram аккаунтами
        telegram_users = TelegramUser.objects.filter(
            is_active=True, notification_settings__enable_daily_reminders=True
        ).select_related("user", "notification_settings")

        for telegram_user in telegram_users:
            try:
                bot_service.send_daily_summary(
                    chat_id=telegram_user.chat_id, user=telegram_user.user
                )

                # Сохраняем в историю
                from telegram_bot.models import SentNotification

                SentNotification.objects.create(
                    telegram_user=telegram_user,
                    notification_type="daily_summary",
                    message_text="Ежедневный отчет",
                    is_delivered=True,
                )

            except Exception as e:
                logger.error(
                    f"Error sending daily summary to {telegram_user.chat_id}: {e}"
                )

    return "Daily summaries sent"


@shared_task
def send_weekly_reports():
    """Отправка еженедельных отчетов (по воскресеньям)"""
    now = timezone.now()

    # Отправляем в воскресенье в 10:00
    if now.weekday() == 6 and now.time().hour == 10 and now.time().minute == 0:
        bot_service = TelegramBotService()

        telegram_users = TelegramUser.objects.filter(
            is_active=True, notification_settings__enable_weekly_reports=True
        ).select_related("user")

        for telegram_user in telegram_users:
            try:
                bot_service.send_weekly_report(
                    chat_id=telegram_user.chat_id, user=telegram_user.user
                )

                # Сохраняем в историю
                from telegram_bot.models import SentNotification

                SentNotification.objects.create(
                    telegram_user=telegram_user,
                    notification_type="weekly_report",
                    message_text="Еженедельный отчет",
                    is_delivered=True,
                )

            except Exception as e:
                logger.error(
                    f"Error sending weekly report to {telegram_user.chat_id}: {e}"
                )

    return "Weekly reports sent"


@shared_task
def check_streak_alerts():
    """Проверка и оповещение о рекордных сериях"""
    bot_service = TelegramBotService()

    telegram_users = TelegramUser.objects.filter(
        is_active=True, notification_settings__enable_streak_alerts=True
    ).select_related("user")

    for telegram_user in telegram_users:
        try:
            user = telegram_user.user
            streak = bot_service._calculate_streak(user)

            # Оповещаем о значительных сериях
            if streak in [3, 7, 14, 21, 30, 60, 90]:
                message = (
                    f"🎉 <b>Поздравляем!</b>\n\n"
                    f"Вы достигли серии из <b>{streak} дней</b> подряд!\n\n"
                    f"💪 Продолжайте в том же духе!\n"
                    f"Это отличный результат!"
                )

                bot_service.send_message(chat_id=telegram_user.chat_id, text=message)

        except Exception as e:
            logger.error(f"Error checking streak for {telegram_user.chat_id}: {e}")

    return "Streak alerts checked"
