import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    help = "Настройка и запуск Telegram бота"

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR(
                    "Токен бота не настроен. Укажите TELEGRAM_BOT_TOKEN в .env"
                )
            )
            return

        # Настраиваем вебхук
        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        if not webhook_url:
            # Генерируем URL для вебхука
            webhook_url = f"https://ваш-домен.com{reverse('telegram-webhook')}"

        try:
            # Устанавливаем вебхук
            response = requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": webhook_url},
                timeout=10,
            )

            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f"Вебхук установлен: {webhook_url}")
                )

                # Получаем информацию о боте
                bot_info = requests.get(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe",
                    timeout=10,
                ).json()

                if bot_info["ok"]:
                    bot = bot_info["result"]
                    self.stdout.write(
                        self.style.SUCCESS(f'Бот запущен: @{bot.get("username")}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("Не удалось получить информацию о боте")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка установки вебхука: {response.text}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка запуска бота: {e}"))
