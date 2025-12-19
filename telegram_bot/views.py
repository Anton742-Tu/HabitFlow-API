import json
import logging

from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import TelegramUser
from .services import TelegramBotService

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Обработчик вебхука от Telegram"""
    try:
        # Парсим данные от Telegram
        data = json.loads(request.body.decode("utf-8"))
        logger.info(f"Получено обновление от Telegram: {data}")

        # Обрабатываем сообщение
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            # Обработка команд
            if text.startswith("/"):
                return handle_command(chat_id, text)
            else:
                # Обработка обычных сообщений
                return handle_message(chat_id, text)

        # Обработка callback query (нажатия на кнопки)
        elif "callback_query" in data:
            callback_query = data["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            data = callback_query["data"]

            return handle_callback_query(chat_id, data)

        return JsonResponse({"status": "ok"})

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return HttpResponse(status=500)


def handle_command(chat_id, text):
    """Обработка команд"""
    bot_service = TelegramBotService()

    if text == "/start":
        message = (
            "👋 Привет! Я бот для трекинга привычек HabitFlow.\n\n"
            "📋 Для подключения к вашему аккаунту:\n"
            "1. Откройте приложение HabitFlow\n"
            "2. Перейдите в настройки профиля\n"
            "3. Скопируйте код подключения\n"
            "4. Отправьте его мне в формате:\n"
            "   <code>/connect ВАШ_КОД</code>\n\n"
            "ℹ️ Команды:\n"
            "/start - Начать работу\n"
            "/help - Помощь\n"
            "/connect - Подключить аккаунт\n"
            "/disconnect - Отключить аккаунт\n"
            "/status - Статус подключения"
        )

        bot_service.send_message(chat_id=chat_id, text=message)

    elif text.startswith("/connect"):
        # Извлекаем код подключения
        parts = text.split()
        if len(parts) != 2:
            bot_service.send_message(
                chat_id=chat_id,
                text="❌ Неверный формат команды. Используйте: /connect КОД_ПОДКЛЮЧЕНИЯ",
            )
            return JsonResponse({"status": "ok"})

        connection_code = parts[1]
        return handle_connection(chat_id, connection_code, bot_service)

    elif text == "/disconnect":
        return handle_disconnect(chat_id, bot_service)

    elif text == "/status":
        return handle_status(chat_id, bot_service)

    elif text == "/help":
        message = (
            "ℹ️ <b>Доступные команды:</b>\n\n"
            "/start - Начало работы\n"
            "/connect КОД - Подключить аккаунт\n"
            "/disconnect - Отключить аккаунт\n"
            "/status - Статус подключения\n"
            "/help - Эта справка\n\n"
            "🔔 После подключения вы будете получать:\n"
            "• Напоминания о привычках\n"
            "• Ежедневные отчеты\n"
            "• Уведомления о прогрессе"
        )

        bot_service.send_message(chat_id=chat_id, text=message)

    else:
        bot_service.send_message(
            chat_id=chat_id,
            text="❌ Неизвестная команда. Используйте /help для списка команд",
        )

    return JsonResponse({"status": "ok"})


def handle_connection(chat_id, connection_code, bot_service):
    """Обработка подключения пользователя"""
    try:
        # Здесь должна быть логика проверки кода подключения
        # Для начала используем простой вариант - ищем пользователя по username
        user = User.objects.filter(username=connection_code).first()

        if not user:
            bot_service.send_message(
                chat_id=chat_id,
                text="❌ Код подключения не найден. Убедитесь что код правильный.",
            )
            return JsonResponse({"status": "ok"})

        # Создаем или обновляем запись TelegramUser
        telegram_user, created = TelegramUser.objects.update_or_create(
            user=user, defaults={"chat_id": chat_id, "username": connection_code}
        )

        if created:
            message = (
                f"✅ Аккаунт успешно подключен!\n\n"
                f"👤 Пользователь: {user.username}\n"
                f"📧 Email: {user.email}\n\n"
                f"🔔 Теперь вы будете получать:\n"
                f"• Напоминания о привычках\n"
                f"• Ежедневные отчеты в 21:00\n"
                f"• Уведомления о прогрессе\n\n"
                f"Используйте /status для проверки подключения."
            )
        else:
            message = (
                "✅ Подключение обновлено!\n\n"
                "Теперь вы будете получать уведомления в этот чат."
            )

        bot_service.send_message(chat_id=chat_id, text=message)

    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        bot_service.send_message(
            chat_id=chat_id, text="❌ Ошибка подключения. Попробуйте позже."
        )

    return JsonResponse({"status": "ok"})


def handle_disconnect(chat_id, bot_service):
    """Отключение аккаунта"""
    try:
        telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()

        if telegram_user:
            telegram_user.delete()
            message = "✅ Аккаунт отключен. Вы больше не будете получать уведомления."
        else:
            message = "ℹ️ Аккаунт не был подключен."

        bot_service.send_message(chat_id=chat_id, text=message)

    except Exception as e:
        logger.error(f"Ошибка отключения: {e}")
        bot_service.send_message(
            chat_id=chat_id, text="❌ Ошибка отключения. Попробуйте позже."
        )

    return JsonResponse({"status": "ok"})


def handle_status(chat_id, bot_service):
    """Проверка статуса подключения"""
    try:
        telegram_user = TelegramUser.objects.filter(chat_id=chat_id).first()

        if telegram_user:
            user = telegram_user.user
            message = (
                f"✅ <b>Аккаунт подключен</b>\n\n"
                f"👤 Пользователь: {user.username}\n"
                f"📧 Email: {user.email}\n"
                f"📅 Привычек: {user.habits.count()}\n"
                f"🔗 Подключено: {telegram_user.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            message = (
                "❌ <b>Аккаунт не подключен</b>\n\n"
                "Для подключения:\n"
                "1. Откройте приложение HabitFlow\n"
                "2. Скопируйте код подключения из настроек\n"
                "3. Отправьте: /connect ВАШ_КОД"
            )

        bot_service.send_message(chat_id=chat_id, text=message)

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")

    return JsonResponse({"status": "ok"})


def handle_message(chat_id, text):
    """Обработка обычных сообщений"""
    bot_service = TelegramBotService()

    # Простой эхо - для тестирования
    bot_service.send_message(
        chat_id=chat_id,
        text=f"Вы сказали: {text}\n\nИспользуйте /help для списка команд",
    )

    return JsonResponse({"status": "ok"})


def handle_callback_query(chat_id, callback_data):
    """Обработка нажатий на inline кнопки"""
    bot_service = TelegramBotService()

    if callback_data.startswith("complete_"):
        # Обработка отметки выполнения привычки
        habit_id = callback_data.replace("complete_", "")
        bot_service.send_message(
            chat_id=chat_id,
            text=f"✅ Привычка {habit_id} отмечена как выполненная!\n\nОбновите приложение для синхронизации.",
        )

    elif callback_data.startswith("postpone_"):
        # Отложить напоминание
        habit_id = callback_data.replace("postpone_", "")
        bot_service.send_message(
            chat_id=chat_id, text="⏰ Напоминание отложено на 15 минут."
        )

    return JsonResponse({"status": "ok"})
