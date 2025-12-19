from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from habits.models import Habit
from telegram_bot.models import TelegramUser
from telegram_bot.services import TelegramBotService

User = get_user_model()


class Command(BaseCommand):
    help = "Отправка тестового напоминания подключенным пользователям"

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, help="Имя пользователя для отправки")
        parser.add_argument("--habit", type=int, help="ID привычки для напоминания")

    def handle(self, *args, **options):
        bot_service = TelegramBotService()

        if options["user"]:
            # Отправляем конкретному пользователю
            user = User.objects.filter(username=options["user"]).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR(f'❌ Пользователь {options["user"]} не найден')
                )
                return

            telegram_user = TelegramUser.objects.filter(user=user).first()
            if not telegram_user:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Пользователь {user.username} не подключен к Telegram"
                    )
                )
                return

            # Получаем или создаем тестовую привычку
            habit = self.get_test_habit(user, options.get("habit"))

            self.send_reminder(telegram_user, habit, bot_service)

        else:
            # Отправляем всем подключенным пользователям
            telegram_users = TelegramUser.objects.filter(is_active=True)

            self.stdout.write(
                f"📨 Отправка тестовых напоминаний {telegram_users.count()} пользователям..."
            )

            for telegram_user in telegram_users:
                # Получаем первую привычку пользователя
                habit = telegram_user.user.habits.first()
                if not habit:
                    habit = self.create_test_habit(telegram_user.user)

                self.send_reminder(telegram_user, habit, bot_service)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Отправлено {telegram_users.count()} напоминаний"
                )
            )

    def get_test_habit(self, user, habit_id=None):
        """Получаем тестовую привычку"""
        if habit_id:
            habit = Habit.objects.filter(id=habit_id, user=user).first()
            if habit:
                return habit

        # Берем первую привычку пользователя
        habit = user.habits.first()
        if not habit:
            # Создаем тестовую привычку
            habit = self.create_test_habit(user)

        return habit

    def create_test_habit(self, user):
        """Создание тестовой привычки если нет ни одной"""
        habit = Habit.objects.create(
            user=user,
            place="Дом",
            time=timezone.now().time(),
            action="Пить воду",
            is_pleasant=False,
            frequency="daily",
            duration=60,
            is_public=False,
        )
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Создана тестовая привычка для {user.username}")
        )
        return habit

    def send_reminder(self, telegram_user, habit, bot_service):
        """Отправка напоминания"""
        try:
            result = bot_service.send_habit_reminder(
                chat_id=telegram_user.chat_id, habit=habit
            )

            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Напоминание отправлено {telegram_user.user.username}"
                    )
                )
                self.stdout.write(f"     Привычка: {habit.action}")
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ Ошибка отправки {telegram_user.user.username}"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Ошибка: {e}"))
