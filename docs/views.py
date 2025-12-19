from django.http import JsonResponse
from django.views.generic import TemplateView

from .manual_endpoints import MANUAL_ENDPOINTS_DOCS


class APIDocumentationView(TemplateView):
    """Страница с полной документацией API"""

    template_name = "docs/api_documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manual_docs"] = MANUAL_ENDPOINTS_DOCS
        return context


def api_spec_json():
    """JSON со спецификацией API (для фронтенда)"""
    spec = {
        "api": {
            "version": "1.0.0",
            "title": "HabitFlow API",
            "description": "API для трекинга привычек по методологии Atomic Habits",
            "base_url": os.getenv("TELEGRAM_BOT_URL", "http://anton_tumashov_bot"),
            "commands": [
                "/start - Начало работы",
                "/connect {код} - Подключить аккаунт",
                "/status - Статус подключения",
                "/stats - Статистика привычек",
                "/help - Справка по командам",
            ],
        },
    }
    return JsonResponse(spec)
