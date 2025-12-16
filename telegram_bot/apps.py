from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "telegram_bot"
    verbose_name = "Telegram Bot"

    def ready(self):
        # Пока не импортируем сигналы, так как их нет
        # Когда создадите signals.py, раскомментируйте:
        # import telegram_bot.signals
        pass
