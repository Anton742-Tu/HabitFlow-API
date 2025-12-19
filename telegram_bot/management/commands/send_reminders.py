from django.core.management.base import BaseCommand

from telegram_bot.tasks import send_scheduled_reminders


class Command(BaseCommand):
    help = "Ручная отправка напоминаний по расписанию"

    def handle(self, *args, **options):
        self.stdout.write("⏰ Отправка запланированных напоминаний...")

        reminders_sent = send_scheduled_reminders()

        self.stdout.write(
            self.style.SUCCESS(f"✅ Отправлено {reminders_sent} напоминаний")
        )
