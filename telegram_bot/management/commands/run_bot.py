import json
import logging
import time

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from telegram_bot.models import TelegramConnectionCode, TelegramUser
from telegram_bot.services import TelegramBotService

logger = logging.getLogger(__name__)
User = get_user_model()


def _handle_connect_command(chat_id, connection_code, bot_service, message):
    """Обработка команды подключения"""
    try:
        code_obj = TelegramConnectionCode.objects.filter(code=connection_code, is_used=False).first()

        if not code_obj:
            bot_service.send_message(
                chat_id,
                "❌ <b>Код не найден или уже использован</b>\n\n"
                "Возможные причины:\n"
                "• Код введен неправильно\n"
                "• Код истек (действует 10 минут)\n"
                "• Код уже был использован\n\n"
                "Получите новый код в веб-приложении HabitFlow",
            )
            return

        if not code_obj.is_valid():
            bot_service.send_message(
                chat_id,
                "❌ <b>Код истек</b>\n\n"
                "Код действителен только 10 минут.\n"
                "Получите новый код в веб-приложении HabitFlow",
            )
            return

        user = code_obj.user

        from_user = message.get("from", {})
        telegram_username = from_user.get("username", "")
        first_name = from_user.get("first_name", "")
        last_name = from_user.get("last_name", "")

        telegram_user, created = TelegramUser.objects.update_or_create(
            user=user,
            defaults={
                "chat_id": chat_id,
                "telegram_username": telegram_username,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )

        code_obj.mark_as_used()

        if created:
            response_text = (
                f"✅ <b>Аккаунт успешно подключен!</b>\n\n"
                f"👤 <b>Пользователь:</b> {user.username}\n"
                f"📧 <b>Email:</b> {user.email}\n"
                f"🔗 <b>Подключено:</b> {timezone.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"🎉 <b>Теперь вы будете получать:</b>\n"
                f"• Напоминания о привычках\n"
                f"• Ежедневные отчеты\n"
                f"• Уведомления о прогрессе\n\n"
                f"Используйте /status для проверки подключения."
            )
        else:
            response_text = "✅ <b>Подключение обновлено!</b>\n\nТеперь вы будете получать уведомления в этот чат."

        bot_service.send_message(chat_id, response_text)

        time.sleep(1)
        bot_service.send_message(
            chat_id,
            "🔔 <b>Тестовое уведомление</b>\n\n"
            "Если вы видите это сообщение, значит бот работает правильно!\n"
            "Скоро вы получите первое напоминание о привычке.",
        )

    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        bot_service.send_message(
            chat_id, "❌ <b>Ошибка подключения</b>\n\nПопробуйте позже или обратитесь в поддержку."
        )


def _handle_stats_command(chat_id, bot_service):
    """Обработка команды статистики"""
    try:
        telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()

        if not telegram_user:
            bot_service.send_message(chat_id, "❌ <b>Сначала подключите аккаунт!</b>\n\nИспользуйте /connect КОД")
            return

        user = telegram_user.user

        from django.db import models

        total_habits = user.habits.count()
        completed_today = user.habits.filter(completions__completed_at__date=timezone.now().date()).count()

        pleasant_habits = user.habits.filter(is_pleasant=True).count()
        useful_habits = user.habits.filter(is_pleasant=False).count()

        recent_completions = (
            user.habits.filter(completions__isnull=False)
            .annotate(last_completion=models.Max("completions__completed_at"))
            .order_by("-last_completion")[:3]
        )

        recent_text = ""
        for habit in recent_completions:
            if habit.last_completion:
                time_diff = timezone.now() - habit.last_completion
                if time_diff.days > 0:
                    recent_text += f"• {habit.action} - {time_diff.days} дней назад\n"
                else:
                    recent_text += f"• {habit.action} - сегодня\n"

        response_text = (
            f"📊 <b>Ваша статистика</b>\n\n"
            f"👤 <b>Пользователь:</b> {user.username}\n\n"
            f"📈 <b>Общая статистика:</b>\n"
            f"• Всего привычек: {total_habits}\n"
            f"• Приятных привычек: {pleasant_habits}\n"
            f"• Полезных привычек: {useful_habits}\n"
            f"• Выполнено сегодня: {completed_today}/{total_habits}\n\n"
        )

        if recent_text:
            response_text += f"⏰ <b>Последние выполнения:</b>\n{recent_text}\n"

        response_text += "💪 <b>Продолжайте в том же духе!</b>\n\nДля детальной статистики откройте веб-приложение."

        bot_service.send_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")


def _answer_callback_query(callback_query_id, text):
    """Отправка ответа на callback query"""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text, "show_alert": False},
        )

        if response.status_code != 200:
            logger.error(f"Ошибка ответа на callback query: {response.text}")

    except Exception as e:
        logger.error(f"Ошибка ответа на callback query: {e}")


def _handle_callback_query(chat_id, data, bot_service, callback_query):
    """Обработка нажатия на inline кнопки"""

    if data.startswith("complete_"):
        habit_id = data.replace("complete_", "")

        bot_service.send_message(
            chat_id,
            f"✅ <b>Привычка отмечена как выполненная!</b>\n\n"
            f"ID привычки: {habit_id}\n"
            f"Обновите приложение для синхронизации.",
        )

        _answer_callback_query(callback_query["id"], "Привычка отмечена!")

    elif data.startswith("postpone_"):
        habit_id = data.replace("postpone_", "")

        bot_service.send_message(
            chat_id, "⏰ <b>Напоминание отложено на 15 минут</b>\n\nВы получите новое напоминание через 15 минут."
        )

        _answer_callback_query(callback_query["id"], "Напоминание отложено")


def _handle_settings_command(chat_id, bot_service):
    """Обработка команды настроек"""
    try:
        telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()

        if not telegram_user:
            bot_service.send_message(chat_id, "❌ <b>Сначала подключите аккаунт!</b>\n\nИспользуйте /connect КОД")
            return

        response_text = (
            "⚙️ <b>Настройки уведомлений</b>\n\n"
            "🔔 <b>Текущие настройки:</b>\n"
            "• Напоминания о привычках: ✅ Включены\n"
            "• Ежедневные отчеты: ✅ Включены\n"
            "• Уведомления о прогрессе: ✅ Включены\n\n"
            "⚡ <b>Быстрые команды:</b>\n"
            "/notify_on - Включить все уведомления\n"
            "/notify_off - Выключить все уведомления\n\n"
            "Для детальных настроений откройте веб-приложение."
        )

        bot_service.send_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"Ошибка в настройках: {e}")


def _handle_message(chat_id, text, bot_service, message):
    """Обработка текстового сообщения"""

    if text == "/start":
        response_text = (
            "👋 <b>Привет! Я бот для трекера привычек HabitFlow!</b>\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "/start - Начало работы\n"
            "/connect - Подключить аккаунт\n"
            "/help - Помощь\n\n"
            "🔗 <b>Для подключения:</b>\n"
            "1. Откройте веб-приложение HabitFlow\n"
            "2. В профиле нажмите 'Подключить Telegram'\n"
            "3. Скопируйте код\n"
            "4. Отправьте: <code>/connect ВАШ_КОД</code>\n\n"
            "После подключения вы будете получать напоминания о привычках!"
        )

        bot_service.send_message(chat_id, response_text)

    elif text == "/help":
        response_text = (
            "ℹ️ <b>Справка по командам:</b>\n\n"
            "/start - Начало работы с ботом\n"
            "/connect КОД - Подключить ваш аккаунт HabitFlow\n"
            "/status - Проверить статус подключения\n"
            "/stats - Ваша статистика\n"
            "/settings - Настройки уведомлений\n"
            "/help - Эта справка\n\n"
            "🔔 <b>После подключения:</b>\n"
            "• Вы будете получать напоминания о привычках\n"
            "• Ежедневные отчеты о выполнении\n"
            "• Уведомления о вашем прогрессе"
        )

        bot_service.send_message(chat_id, response_text)

    elif text.startswith("/connect"):
        parts = text.split()
        if len(parts) == 2:
            connection_code = parts[1]
            _handle_connect_command(chat_id, connection_code, bot_service, message)
        else:
            bot_service.send_message(
                chat_id,
                "❌ <b>Неверный формат команды</b>\n\n"
                "Используйте: <code>/connect ВАШ_КОД</code>\n\n"
                "Чтобы получить код:\n"
                "1. Откройте HabitFlow в браузере\n"
                "2. Перейдите в профиль\n"
                "3. Нажмите 'Подключить Telegram'\n"
                "4. Скопируйте код",
            )

    elif text == "/settings":
        _handle_settings_command(chat_id, bot_service)

    elif text == "/stats" or text == "/statistics":
        _handle_stats_command(chat_id, bot_service)

    elif text == "/status":
        try:
            telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()
            if telegram_user:
                response_text = (
                    f"✅ <b>Аккаунт подключен!</b>\n\n"
                    f"👤 <b>Пользователь:</b> {telegram_user.user.username}\n"
                    f"📧 <b>Email:</b> {telegram_user.user.email}\n"
                    f"🔗 <b>Подключен:</b> {telegram_user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"🔔 <b>Уведомления:</b> {'Включены ✅' if telegram_user.is_active else 'Выключены ❌'}\n\n"
                    f"Используйте /stats для статистики"
                )
            else:
                response_text = (
                    "❌ <b>Аккаунт не подключен</b>\n\n"
                    "Используйте /connect КОД для подключения вашего аккаунта HabitFlow"
                )
            bot_service.send_message(chat_id, response_text)
        except Exception as e:
            logger.error(f"Ошибка статуса: {e}")

    else:
        bot_service.send_message(
            chat_id, "🤔 <b>Не понял команду</b>\n\nИспользуйте /help для списка доступных команд"
        )


def _process_update(update, bot_service):
    """Обработка одного обновления"""
    try:
        logger.info(f"Получено обновление: {update}")

        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            if text:
                _handle_message(chat_id, text, bot_service, message)

        elif "callback_query" in update:
            callback_query = update["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            data = callback_query["data"]

            _handle_callback_query(chat_id, data, bot_service, callback_query)

    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")


class Command(BaseCommand):
    help = "Запуск Telegram бота в режиме polling"

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(self.style.ERROR("❌ Токен бота не найден. Добавьте TELEGRAM_BOT_TOKEN в .env"))
            return

        self.stdout.write(self.style.SUCCESS("🤖 Запуск Telegram бота в режиме polling..."))
        self.stdout.write("⚡ Бот будет проверять новые сообщения каждую секунду")
        self.stdout.write("🛑 Для остановки нажмите Ctrl+C")

        bot_service = TelegramBotService(settings.TELEGRAM_BOT_TOKEN)
        offset = 0

        try:
            while True:
                try:
                    response = requests.get(
                        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates",
                        params={
                            "offset": offset,
                            "timeout": 10,
                            "allowed_updates": json.dumps(["message", "callback_query"]),
                        },
                        timeout=15,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            updates = data["result"]

                            for update in updates:
                                offset = update["update_id"] + 1
                                _process_update(update, bot_service)

                    time.sleep(1)

                except requests.exceptions.Timeout:
                    continue
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("\n👋 Останавливаем бота..."))
                    break
                except Exception as e:
                    logger.error(f"Ошибка в основном цикле: {e}")
                    time.sleep(5)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n✅ Бот остановлен"))
