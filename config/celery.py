import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("habitflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Расписание для задач
app.conf.beat_schedule = {
    # Напоминания о привычках - каждые 5 минут
    "send-habit-reminders": {
        "task": "habits.tasks.send_habit_reminders",
        "schedule": crontab(minute="*/5"),
    },
    # Ежедневные отчеты - в 21:00
    "send-daily-summaries": {
        "task": "habits.tasks.send_daily_summaries",
        "schedule": crontab(hour=21, minute=0),
    },
    # Еженедельные отчеты - по воскресеньям в 10:00
    "send-weekly-reports": {
        "task": "habits.tasks.send_weekly_reports",
        "schedule": crontab(day_of_week=0, hour=10, minute=0),
    },
    # Проверка серий - каждый день в 9:00
    "check-streak-alerts": {
        "task": "habits.tasks.check_streak_alerts",
        "schedule": crontab(hour=9, minute=0),
    },
}
