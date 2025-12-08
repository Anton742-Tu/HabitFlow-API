import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .models import TelegramConnectionCode, TelegramUser
from .services import TelegramBotService

logger = logging.getLogger(__name__)

# Инициализируем сервис
bot_service = TelegramBotService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я — бот HabitFlow, помогаю формировать полезные привычки.\n\n"
        f"📋 <b>Доступные команды:</b>\n"
        f"/start — начало работы\n"
        f"/help — справка\n"
        f"/connect — привязать аккаунт\n"
        f"/habits — мои привычки\n"
        f"/today — задачи на сегодня\n"
        f"/report — статистика\n\n"
        f"Для начала работы привяжите свой аккаунт командой /connect"
    )

    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /connect"""
    from users.models import User

    user = update.effective_user

    # Проверяем, не привязан ли уже Telegram
    try:
        telegram_user = TelegramUser.objects.get(telegram_id=user.id)
        await update.message.reply_text(
            f"✅ Ваш аккаунт уже привязан к пользователю {telegram_user.django_user.username}", parse_mode="HTML"
        )
        return
    except TelegramUser.DoesNotExist:
        pass

    # Создаем код привязки
    # Находим пользователя по username или email из аргументов
    if context.args:
        identifier = context.args[0]
        try:
            django_user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                django_user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                await update.message.reply_text(
                    "❌ Пользователь не найден. Укажите username или email после команды, например:\n"
                    "/connect ваш_username",
                    parse_mode="HTML",
                )
                return
    else:
        # Если не указан пользователь, показываем инструкцию
        await update.message.reply_text(
            "🔗 <b>Привязка аккаунта</b>\n\n"
            "Чтобы привязать Telegram к вашему аккаунту HabitFlow:\n"
            "1. Зайдите в веб-приложение HabitFlow\n"
            "2. Перейдите в настройки профиля\n"
            "3. Скопируйте код привязки\n"
            "4. Отправьте его мне\n\n"
            "Или укажите ваш username после команды:\n"
            "<code>/connect ваш_username</code>",
            parse_mode="HTML",
        )
        return

    # Создаем код привязки
    connection_code = TelegramConnectionCode.objects.create(django_user=django_user)

    await update.message.reply_text(
        f"🔐 <b>Код привязки создан</b>\n\n"
        f"Ваш код: <code>{connection_code.code}</code>\n"
        f"Действителен до: {connection_code.expires_at.strftime('%H:%M:%S')}\n\n"
        f"1. Зайдите в веб-приложение HabitFlow\n"
        f"2. Введите этот код в настройках профиля\n"
        f"3. Или введите код здесь",
        parse_mode="HTML",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    text = update.message.text

    # Проверяем, не является ли сообщение кодом привязки
    if text.isdigit() and len(text) == 6:
        await handle_connection_code(update, text)
        return

    await update.message.reply_text(
        f"Я пока понимаю только команды 😊\n" f"Используйте /help чтобы увидеть список команд"
    )


async def handle_connection_code(update: Update, code: str):
    """Обработка кода привязки"""
    try:
        connection_code = TelegramConnectionCode.objects.get(code=code, is_used=False, telegram_id__isnull=True)

        # Проверяем срок действия
        if not connection_code.is_valid():
            await update.message.reply_text("❌ Срок действия кода истек")
            return

        # Привязываем Telegram
        TelegramUser.objects.create(
            django_user=connection_code.django_user,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
        )

        # Помечаем код как использованный
        connection_code.telegram_id = update.effective_user.id
        connection_code.is_used = True
        connection_code.save()

        await update.message.reply_text(
            f"✅ Отлично! Ваш Telegram успешно привязан к аккаунту "
            f"{connection_code.django_user.username}.\n\n"
            f"Теперь вы будете получать напоминания о привычках!",
            parse_mode="HTML",
        )

    except TelegramConnectionCode.DoesNotExist:
        await update.message.reply_text("❌ Неверный или уже использованный код")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов (нажатия на кнопки)"""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat_id

    # Обработка кнопки "Выполнено"
    if data.startswith("complete_"):
        habit_id = data.replace("complete_", "")
        # Здесь должна быть логика отметки выполнения привычки
        await query.edit_message_text(text=f"✅ Привычка отмечена как выполненная!", parse_mode="HTML")

    # Обработка кнопки "Отложить"
    elif data.startswith("postpone_"):
        habit_id = data.replace("postpone_", "")
        # Здесь должна быть логика откладывания напоминания
        await query.edit_message_text(text=f"⏰ Напоминание отложено на 15 минут", parse_mode="HTML")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("😕 Произошла ошибка. Попробуйте позже.")


def setup_handlers(application: Application):
    """Настройка обработчиков"""
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))  # Пока то же самое
    application.add_handler(CommandHandler("connect", connect_command))

    # Обработка callback запросов (кнопки)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Обработка текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    application.add_error_handler(error_handler)
