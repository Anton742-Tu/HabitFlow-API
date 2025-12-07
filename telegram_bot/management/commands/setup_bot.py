import subprocess
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Настройка Telegram бота и вебхука"

    def add_arguments(self, parser):
        parser.add_argument("--use-ngrok", action="store_true", help="Использовать ngrok для туннелирования")
        parser.add_argument("--ngrok-auth", type=str, help="Токен аутентификации ngrok (необязательно)")

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN

        if not token:
            self.stdout.write(self.style.ERROR("❌ Токен бота не найден. Добавьте TELEGRAM_BOT_TOKEN в .env"))
            return

        # Проверяем бота
        if not self.check_bot(token):
            return

        # Настраиваем вебхук
        if options["use_ngrok"]:
            self.setup_with_ngrok(token, options["ngrok_auth"])
        else:
            self.setup_webhook(token)

    def check_bot(self, token):
        """Проверка доступности бота"""
        try:
            self.stdout.write("🔍 Проверяем доступность бота...")
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Бот найден!\n"
                            f'   Имя: {bot_info["first_name"]}\n'
                            f'   Username: @{bot_info.get("username", "N/A")}\n'
                            f'   ID: {bot_info["id"]}'
                        )
                    )
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Ошибка API: {data.get("description")}'))
                    return False
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP ошибка: {response.status_code}"))
                return False

        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("❌ Нет подключения к интернету"))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
            return False

    def setup_webhook(self, token, webhook_url=None):
        """Настройка вебхука напрямую"""
        self.stdout.write("\n🔗 Настраиваем вебхук...")

        if not webhook_url:
            webhook_url = settings.TELEGRAM_WEBHOOK_URL

        if not webhook_url:
            self.stdout.write(self.style.WARNING("⚠️ TELEGRAM_WEBHOOK_URL не указан."))
            self.show_ngrok_instructions()
            return

        # Устанавливаем вебхук
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/setWebhook", json={"url": webhook_url}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.stdout.write(self.style.SUCCESS(f"✅ Вебхук установлен: {webhook_url}"))
                    self.show_webhook_info(token)
                else:
                    error_msg = data.get("description", "Неизвестная ошибка")
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка установки вебхука: {error_msg}"))
                    self.debug_webhook_error(token, webhook_url)
            else:
                self.stdout.write(self.style.ERROR(f"❌ HTTP ошибка {response.status_code} при установке вебхука"))
                self.debug_webhook_error(token, webhook_url)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))

    def setup_with_ngrok(self, token, ngrok_auth=None):
        """Настройка с использованием ngrok"""
        self.stdout.write("\n🌐 Запускаем ngrok туннель...")

        try:
            # Запускаем ngrok
            ngrok_process = subprocess.Popen(
                ["ngrok", "http", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Даем ngrok время запуститься
            time.sleep(3)

            # Получаем ngrok URL
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    https_tunnel = next((t for t in tunnels if t["proto"] == "https"), None)

                    if https_tunnel:
                        webhook_url = f"{https_tunnel['public_url']}/telegram/webhook/telegram/"

                        self.stdout.write(self.style.SUCCESS(f"🌐 Ngrok туннель запущен: {webhook_url}"))

                        # Устанавливаем вебхук
                        self.setup_webhook(token, webhook_url)

                        # Ждем завершения
                        self.stdout.write("\n🔄 Ngrok работает. Нажмите Ctrl+C для остановки...")
                        ngrok_process.wait()
                    else:
                        self.stdout.write(self.style.ERROR("❌ Не найден HTTPS туннель ngrok"))
                        ngrok_process.terminate()
                else:
                    self.stdout.write(self.style.ERROR("❌ Не удалось получить URL ngrok"))
                    ngrok_process.terminate()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка получения ngrok URL: {e}"))
                ngrok_process.terminate()

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ Ngrok не установлен. Скачайте с https://ngrok.com/download"))
            self.show_ngrok_instructions()

    def show_webhook_info(self, token):
        """Показывает информацию о вебхуке"""
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    webhook_info = data["result"]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n📊 Информация о вебхуке:\n"
                            f'   URL: {webhook_info.get("url", "N/A")}\n'
                            f'   Ошибок: {webhook_info.get("last_error_message", "Нет")}\n'
                            f'   Обновлений в очереди: {webhook_info.get("pending_update_count", 0)}'
                        )
                    )
        except:
            pass

    def debug_webhook_error(self, token, webhook_url):
        """Отладка ошибок вебхука"""
        self.stdout.write("\n🔍 Отладка ошибки вебхука:")
        self.stdout.write(f"   URL: {webhook_url}")
        self.stdout.write(f"   Токен: {token[:10]}...")

        # Проверяем доступность URL
        try:
            test_response = requests.get(webhook_url.replace("/telegram/webhook/telegram/", ""), timeout=5)
            self.stdout.write(f"   Доступность сервера: ✅ HTTP {test_response.status_code}")
        except:
            self.stdout.write("   Доступность сервера: ❌ Недоступен")

        # Проверяем что URL заканчивается правильно
        if not webhook_url.endswith("/"):
            self.stdout.write("   ❌ URL должен заканчиваться на /")

        # Проверяем что используется HTTPS
        if not webhook_url.startswith("https://"):
            self.stdout.write("   ⚠️ Для production требуется HTTPS")

    def show_ngrok_instructions(self):
        """Показывает инструкции по настройке ngrok"""
        self.stdout.write("\n📖 Инструкции по настройке ngrok:")
        self.stdout.write("   1. Скачайте ngrok: https://ngrok.com/download")
        self.stdout.write("   2. Распакуйте в удобную папку")
        self.stdout.write("   3. Добавьте в PATH или запускайте из папки")
        self.stdout.write("   4. Запустите Django сервер: python manage.py runserver")
        self.stdout.write("   5. В другом терминале запустите: ngrok http 8000")
        self.stdout.write("   6. Скопируйте HTTPS URL (например: https://abc123.ngrok.io)")
        self.stdout.write("   7. Запустите: python manage.py setup_bot --use-ngrok")
