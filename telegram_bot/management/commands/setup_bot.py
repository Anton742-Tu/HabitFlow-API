import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Настройка Telegram бота (webhook)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            type=str,
            required=True,
            help="Домен для webhook (например, https://example.com)",
        )
        parser.add_argument(
            "--secret-token",
            type=str,
            help="Секретный токен для проверки webhook (опционально)",
        )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        domain = options["domain"]
        secret_token = options.get("secret_token")

        if not token:
            self.stdout.write(self.style.ERROR("❌ TELEGRAM_BOT_TOKEN не настроен"))
            return

        webhook_url = f"{domain}/telegram/webhook/"

        self.stdout.write("🌐 Настройка webhook для бота...")
        self.stdout.write(f"📡 Webhook URL: {webhook_url}")
        self.stdout.write(f"🔑 Секретный токен: {secret_token or 'не установлен'}")

        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }

        if secret_token:
            payload["secret_token"] = secret_token

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    self.stdout.write(
                        self.style.SUCCESS("✅ Webhook успешно настроен!")
                    )

                    # Получаем информацию о webhook
                    info_response = requests.get(
                        f"https://api.telegram.org/bot{token}/getWebhookInfo",
                        timeout=10,
                    )

                    if info_response.status_code == 200:
                        webhook_info = info_response.json()
                        if webhook_info.get("ok"):
                            info = webhook_info["result"]
                            self.stdout.write("📊 Информация о webhook:")
                            self.stdout.write(
                                f"   URL: {info.get('url', 'не настроен')}"
                            )
                            self.stdout.write(
                                f"   Есть сертификат: {info.get('has_custom_certificate', False)}"
                            )
                            self.stdout.write(
                                f"   Ожидает обновлений: {info.get('pending_update_count', 0)}"
                            )
                            self.stdout.write(
                                f"   Последняя ошибка: {info.get('last_error_message', 'нет')}"
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    "⚠️ Не удалось получить информацию о webhook"
                                )
                            )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Ошибка настройки webhook: {result.get('description', 'Unknown error')}"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ HTTP ошибка: {response.status_code}")
                )

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка подключения: {e}"))
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            self.stdout.write(self.style.ERROR(f"❌ Неожиданная ошибка: {e}"))

        self.stdout.write("\n📋 Следующие шаги:")
        self.stdout.write("1. Убедитесь, что ваш домен доступен из интернета")
        self.stdout.write("2. Настройте SSL сертификат (обязательно для Telegram)")
        self.stdout.write("3. Запустите Django сервер на указанном домене")
        self.stdout.write("4. Проверьте работу бота, отправив ему /start")
