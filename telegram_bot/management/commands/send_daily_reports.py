from django.core.management.base import BaseCommand
from django.utils import timezone

from habits.models import HabitCompletion
from telegram_bot.models import TelegramUser
from telegram_bot.services import TelegramBotService


class Command(BaseCommand):
    help = "Отправка ежедневных отчетов пользователям"

    def handle(self, *args, **options):
        bot_service = TelegramBotService()
        today = timezone.now().date()

        # Находим всех подключенных пользователей
        telegram_users = TelegramUser.objects.filter(is_active=True)

        self.stdout.write(f"📊 Отправка ежедневных отчетов {telegram_users.count()} пользователям...")

        for telegram_user in telegram_users:
            try:
                user = telegram_user.user

                # Статистика за сегодня
                completions_today = HabitCompletion.objects.filter(habit__user=user, completed_at__date=today).count()

                total_habits = user.habits.count()
                completion_rate = (completions_today / total_habits * 100) if total_habits > 0 else 0

                # Привычки на завтра
                tomorrow_habits = user.habits.order_by("time")[:3]

                tomorrow_text = (
                    "\n".join([f"• {h.time.strftime('%H:%M')} - {h.action}" for h in tomorrow_habits])
                    if tomorrow_habits
                    else "На завтра привычек нет"
                )

                message = (
                    f"📅 <b>Ежедневный отчет</b>\n"
                    f"Дата: {today.strftime('%d.%m.%Y')}\n\n"
                    f"📈 <b>Статистика за день:</b>\n"
                    f"✅ Выполнено: {completions_today}/{total_habits}\n"
                    f"📊 Процент: {completion_rate:.1f}%\n\n"
                    f"⏰ <b>Привычки на завтра:</b>\n"
                    f"{tomorrow_text}\n\n"
                    f"💪 Отличная работа! Продолжайте формировать полезные привычки!"
                )

                bot_service.send_message(telegram_user.chat_id, message)
                self.stdout.write(self.style.SUCCESS(f"  ✅ Отчет отправлен {user.username}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Ошибка для {telegram_user.user.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Отправлено {telegram_users.count()} ежедневных отчетов"))
