from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from telegram_bot.models import TelegramUser
from telegram_bot.services import TelegramBotService

User = get_user_model()


class Command(BaseCommand):
    help = "Тестовая отправка уведомления"

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, help="Имя пользователя для отправки теста")
        parser.add_argument("--all", action="store_true", help="Отправить всем подключенным пользователям")

    def handle(self, *args, **options):
        bot_service = TelegramBotService()

        if options["user"]:
            # Отправляем конкретному пользователю
            user = User.objects.filter(username=options["user"]).first()
            if not user:
                self.stdout.write(self.style.ERROR(f'❌ Пользователь {options["user"]} не найден'))
                return

            telegram_user = TelegramUser.objects.filter(user=user).first()
            if not telegram_user:
                self.stdout.write(self.style.ERROR(f"❌ Пользователь {user.username} не подключен к Telegram"))
                return

            self.send_test_notification(telegram_user.chat_id, bot_service, user)

        elif options["all"]:
            # Отправляем всем подключенным пользователям
            telegram_users = TelegramUser.objects.filter(is_active=True)

            self.stdout.write(f"📨 Отправка тестовых уведомлений {telegram_users.count()} пользователям...")

            for telegram_user in telegram_users:
                self.send_test_notification(telegram_user.chat_id, bot_service, telegram_user.user)

            self.stdout.write(self.style.SUCCESS(f"✅ Отправлено {telegram_users.count()} уведомлений"))

        else:
            # Показываем подключенных пользователей
            telegram_users = TelegramUser.objects.filter(is_active=True)

            self.stdout.write("📱 Подключенные пользователи:")
            for telegram_user in telegram_users:
                habits_count = telegram_user.user.habits.count()
                self.stdout.write(
                    f"  👤 {telegram_user.user.username} "
                    f'({telegram_user.telegram_username or "без username"}) '
                    f"- {habits_count} привычек"
                )

            self.stdout.write("\n📝 Использование:")
            self.stdout.write("  python manage.py test_notification --user username")
            self.stdout.write("  python manage.py test_notification --all")

    def send_test_notification(self, chat_id, bot_service, user):
        """Отправка тестового уведомления"""
        try:
            # Отправляем простое тестовое сообщение
            message = (
                "🧪 <b>Тестовое уведомление от HabitFlow</b>\n\n"
                "✅ <b>Бот работает корректно!</b>\n\n"
                "📊 <b>Ваша статистика:</b>\n"
                f"   • Привычек: {user.habits.count()}\n"
                f"   • Приятных привычек: {user.habits.filter(is_pleasant=True).count()}\n"
                f"   • Полезных привычек: {user.habits.filter(is_pleasant=False).count()}\n\n"
                "🔔 <b>Скоро вы получите:</b>\n"
                "• Напоминания о привычках\n"
                "• Ежедневные отчеты\n"
                "• Уведомления о прогрессе"
            )

            result = bot_service.send_message(chat_id, message)

            if result:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Отправлено {user.username}"))
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ Ошибка отправки {user.username}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Ошибка: {e}"))
