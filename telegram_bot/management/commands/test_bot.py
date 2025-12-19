import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Тестирование подключения Telegram бота"

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN

        if not token:
            self.stdout.write(self.style.ERROR("Токен бота не найден в настройках"))
            self.stdout.write("Добавьте в .env: TELEGRAM_BOT_TOKEN=ваш_токен")
            return

        try:
            # Проверяем что бот доступен
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Бот подключен!\n"
                            f'Имя: {bot_info["first_name"]}\n'
                            f'Username: @{bot_info.get("username", "N/A")}\n'
                            f'ID: {bot_info["id"]}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Ошибка API: {data.get("description")}')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"HTTP ошибка: {response.status_code}")
                )

        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("Нет подключения к интернету"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
