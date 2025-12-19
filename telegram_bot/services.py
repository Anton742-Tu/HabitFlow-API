import logging
from typing import Any, Dict

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Сервис для работы с Telegram Bot API"""

    def __init__(self, token=None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        if not self.token:
            logger.warning("Telegram bot token is not configured")

    def send_message(self, chat_id, text, parse_mode="HTML", reply_markup=None):
        """Отправка сообщения в Telegram"""
        if not self.token:
            logger.error("Cannot send message: Telegram bot token not configured")
            return None

        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }

            if reply_markup:
                payload["reply_markup"] = reply_markup

            response = requests.post(
                f"{self.base_url}/sendMessage", json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    self.logger.info(f"Сообщение отправлено в Telegram chat {chat_id}")
                    return True  # ← Должен возвращать True
                else:
                    self.logger.error(f"Telegram API error: {data.get('description')}")
                    return False  # ← Должен возвращать False
            else:
                self.logger.error(
                    f"Telegram API error: {response.status_code} - {response.text}"
                )
                return False  # ← Должен возвращать False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Telegram message: {e}")
            return False  # ← Должен возвращать False

    def send_habit_reminder(self, chat_id, habit):
        """Отправка напоминания о привычке"""
        time_str = habit.time.strftime("%H:%M") if habit.time else "??:??"

        message = (
            f"⏰ <b>Время для привычки!</b>\n\n"
            f"📋 <b>Действие:</b> {habit.action}\n"
            f"🕐 <b>Время:</b> {time_str}\n"
            f"📍 <b>Место:</b> {habit.place}\n"
            f"⏱️ <b>Длительность:</b> {habit.duration} секунд\n\n"
            f'<i>"{habit.full_description}"</i>'
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Выполнено", "callback_data": f"complete_{habit.id}"},
                    {
                        "text": "⏰ Отложить на 15 мин",
                        "callback_data": f"postpone_{habit.id}",
                    },
                ]
            ]
        }

        return self.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)

    def send_daily_summary(self, chat_id: int, user) -> Dict[str, Any]:
        """Отправка ежедневного отчета"""

        from habits.models import HabitCompletion

        today = timezone.now().date()
        completions_today = HabitCompletion.objects.filter(
            habit__user=user, completed_at__date=today
        ).count()

        total_habits = user.habits.count()
        completion_rate = (
            (completions_today / total_habits * 100) if total_habits > 0 else 0
        )

        # Находим ближайшие привычки
        now = timezone.now()
        next_habits = user.hits.filter(time__gt=now.time()).order_by("time")[:3]

        next_habits_text = (
            "\n".join(
                [f"• {h.time.strftime('%H:%M')} - {h.action}" for h in next_habits]
            )
            if next_habits
            else "На сегодня привычек больше нет! 🎉"
        )

        message = (
            f"📊 <b>Ежедневный отчет</b>\n\n"
            f"📈 <b>Статистика за день:</b>\n"
            f"   ✅ Выполнено: {completions_today}/{total_habits}\n"
            f"   📊 Процент: {completion_rate:.1f}%\n\n"
            f"⏰ <b>Ближайшие привычки:</b>\n"
            f"{next_habits_text}\n\n"
            f"💪 Продолжайте в том же духе!"
        )

        return self.send_message(chat_id=chat_id, text=message)

    def send_weekly_report(self, chat_id: int, user) -> Dict[str, Any]:
        """Отправка еженедельного отчета"""
        from datetime import timedelta

        from django.db.models import Count

        from habits.models import HabitCompletion

        week_ago = timezone.now() - timedelta(days=7)

        # Статистика за неделю
        weekly_completions = HabitCompletion.objects.filter(
            habit__user=user, completed_at__gte=week_ago
        ).count()

        # Процент выполнения
        habits = user.habits.all()
        total_expected = sum(7 / h.frequency_days for h in habits)
        completion_rate = (
            (weekly_completions / total_expected * 100) if total_expected > 0 else 0
        )

        # Самая успешная привычка
        successful_habit = (
            habits.annotate(completion_count=Count("completions"))
            .order_by("-completion_count")
            .first()
        )

        # Длиннейшая серия
        streak = self._calculate_streak(user)

        message = (
            f"📅 <b>Еженедельный отчет</b>\n\n"
            f"📈 <b>Статистика за неделю:</b>\n"
            f"   ✅ Выполнений: {weekly_completions}\n"
            f"   📊 Процент: {completion_rate:.1f}%\n"
            f"   🔥 Серия: {streak} дней\n\n"
            f"🏆 <b>Самая успешная привычка:</b>\n"
            f"   {successful_habit.action if successful_habit else 'Нет данных'}\n\n"
            f"💪 Отличная работа! Продолжайте формировать полезные привычки!"
        )

        return self.send_message(chat_id=chat_id, text=message)

    def _calculate_streak(self, user):
        """Рассчет текущей серии последовательных дней"""
        from datetime import timedelta

        from habits.models import HabitCompletion

        # Получаем все уникальные даты выполнения за последние 30 дней
        month_ago = timezone.now() - timedelta(days=30)

        completion_dates = (
            HabitCompletion.objects.filter(
                habit__user=user, completed_at__gte=month_ago
            )
            .dates("completed_at", "day")
            .order_by("-completed_at")
        )

        if not completion_dates:
            return 0

        # Находим самую длинную последовательность
        streak = 1
        current_date = completion_dates[0]

        for next_date in completion_dates[1:]:
            if (current_date - next_date).days == 1:
                streak += 1
                current_date = next_date
            else:
                break

        return streak
