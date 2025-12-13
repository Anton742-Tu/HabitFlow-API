# docs/views.py
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


def api_spec_json(request):
    """JSON со спецификацией API (для фронтенда)"""
    spec = {
        "api": {
            "version": "1.0.0",
            "title": "HabitFlow API",
            "description": "API для трекинга привычек по методологии Atomic Habits",
            "base_url": "http://localhost:8000/api/",
            "authentication": {
                "type": "JWT",
                "endpoint": "/api/users/token/",
                "header": "Authorization: Bearer {token}",
            },
            "endpoints": {
                "users": {
                    "register": {
                        "method": "POST",
                        "url": "/api/users/register/",
                        "description": "Регистрация нового пользователя",
                    },
                    "login": {"method": "POST", "url": "/api/users/token/", "description": "Получение JWT токена"},
                    "profile": {"method": "GET", "url": "/api/users/profile/", "description": "Профиль пользователя"},
                    "telegram_connect": {
                        "method": "GET",
                        "url": "/api/users/telegram/connect/",
                        "description": "Получить код для подключения Telegram",
                    },
                    "logout": {
                        "method": "POST",
                        "url": "/api/users/logout/",
                        "description": "Выход из системы (blacklist refresh token)",
                    },
                    "token_refresh": {
                        "method": "POST",
                        "url": "/api/users/token/refresh/",
                        "description": "Обновление access токена",
                    },
                },
                "habits": {
                    "list": {
                        "method": "GET",
                        "url": "/api/habits/",
                        "description": "Список привычек (свои + публичные)",
                        "query_params": {
                            "page": "Номер страницы",
                            "page_size": "Количество на странице (макс. 50)",
                            "is_pleasant": "Фильтр по типу привычки",
                            "frequency": "Фильтр по периодичности (daily, weekly, monthly)",
                            "is_public": "Фильтр по публичности",
                            "date_from": "Фильтр по дате создания (>=)",
                            "date_to": "Фильтр по дате создания (<=)",
                        },
                    },
                    "create": {"method": "POST", "url": "/api/habits/", "description": "Создать привычку"},
                    "retrieve": {
                        "method": "GET",
                        "url": "/api/habits/{id}/",
                        "description": "Получить детали привычки",
                    },
                    "update": {"method": "PUT/PATCH", "url": "/api/habits/{id}/", "description": "Обновить привычку"},
                    "delete": {"method": "DELETE", "url": "/api/habits/{id}/", "description": "Удалить привычку"},
                    "my_habits": {
                        "method": "GET",
                        "url": "/api/habits/my_habits/",
                        "description": "Только мои привычки",
                    },
                    "public": {
                        "method": "GET",
                        "url": "/api/habits/public/",
                        "description": "Только публичные привычки",
                    },
                    "complete": {
                        "method": "POST",
                        "url": "/api/habits/{id}/complete/",
                        "description": "Отметить выполнение привычки",
                    },
                    "toggle_public": {
                        "method": "PATCH",
                        "url": "/api/habits/{id}/toggle_public/",
                        "description": "Переключить статус публичности",
                    },
                    "stats": {"method": "GET", "url": "/api/habits/stats/", "description": "Статистика выполнения"},
                    "progress": {
                        "method": "GET",
                        "url": "/api/habits/{id}/progress/",
                        "description": "Прогресс конкретной привычки",
                    },
                    "export": {
                        "method": "GET",
                        "url": "/api/habits/export/",
                        "description": "Экспорт привычек (форматы: csv, json)",
                        "query_params": {"format": "Формат экспорта (csv или json)"},
                    },
                    "bulk_complete": {
                        "method": "POST",
                        "url": "/api/habits/bulk_complete/",
                        "description": "Массовое выполнение привычек",
                    },
                },
                "completions": {
                    "list": {"method": "GET", "url": "/api/completions/", "description": "Список выполнений привычек"},
                    "create": {
                        "method": "POST",
                        "url": "/api/completions/",
                        "description": "Создать запись о выполнении",
                    },
                    "delete": {
                        "method": "DELETE",
                        "url": "/api/completions/{id}/",
                        "description": "Удалить запись о выполнении",
                    },
                },
            },
            "models": {
                "Habit": {
                    "description": "Модель привычки пользователя",
                    "fields": {
                        "id": {"type": "integer", "readonly": True, "description": "ID привычки"},
                        "user": {"type": "object", "readonly": True, "description": "Владелец привычки"},
                        "place": {"type": "string", "required": True, "description": "Место выполнения"},
                        "time": {
                            "type": "time",
                            "required": True,
                            "format": "HH:MM",
                            "description": "Время выполнения",
                        },
                        "action": {
                            "type": "string",
                            "required": True,
                            "max_length": 500,
                            "description": "Конкретное действие",
                        },
                        "is_pleasant": {"type": "boolean", "default": False, "description": "Приятная привычка"},
                        "related_habit": {
                            "type": "integer",
                            "optional": True,
                            "description": "Связанная привычка (только для полезных)",
                        },
                        "reward": {
                            "type": "string",
                            "optional": True,
                            "description": "Вознаграждение (только для полезных)",
                        },
                        "frequency": {
                            "type": "string",
                            "required": True,
                            "choices": ["daily", "weekly", "monthly"],
                            "description": "Периодичность выполнения",
                        },
                        "duration": {
                            "type": "integer",
                            "required": True,
                            "max": 120,
                            "description": "Время на выполнение в секундах",
                        },
                        "is_public": {"type": "boolean", "default": False, "description": "Публичная привычка"},
                        "created_at": {"type": "datetime", "readonly": True, "description": "Дата создания"},
                        "updated_at": {"type": "datetime", "readonly": True, "description": "Дата обновления"},
                        "full_description": {
                            "type": "string",
                            "readonly": True,
                            "description": "Полное описание в формате 'Я буду {действие} в {время} в {место}'",
                        },
                        "completions": {"type": "array", "readonly": True, "description": "История выполнений"},
                    },
                },
                "HabitCompletion": {
                    "description": "Модель выполнения привычки",
                    "fields": {
                        "id": {"type": "integer", "readonly": True, "description": "ID выполнения"},
                        "habit": {"type": "integer", "required": True, "description": "Привычка"},
                        "completed_at": {
                            "type": "datetime",
                            "readonly": True,
                            "description": "Дата и время выполнения",
                        },
                        "is_completed": {"type": "boolean", "default": True, "description": "Флаг выполнения"},
                        "note": {"type": "string", "optional": True, "description": "Заметка о выполнении"},
                    },
                },
                "User": {
                    "description": "Модель пользователя",
                    "fields": {
                        "id": {"type": "integer", "readonly": True},
                        "username": {"type": "string", "required": True, "unique": True},
                        "email": {"type": "string", "required": True, "unique": True},
                        "first_name": {"type": "string", "optional": True},
                        "last_name": {"type": "string", "optional": True},
                        "habits_count": {
                            "type": "integer",
                            "readonly": True,
                            "description": "Количество привычек пользователя",
                        },
                        "public_habits_count": {
                            "type": "integer",
                            "readonly": True,
                            "description": "Количество публичных привычек",
                        },
                    },
                },
            },
            "validation_rules": {
                "atomic_habits": [
                    "⏱️ Время выполнения ≤ 120 секунд",
                    "❌ Нельзя одновременно указывать и связанную привычку и вознаграждение",
                    "😊 Связанные привычки должны быть приятными",
                    "🎯 У приятной привычки не может быть вознаграждения или связанной привычки",
                    "📅 Нельзя выполнять привычку реже 1 раза в 7 дней",
                    "⏰ Нельзя не выполнять привычку более 7 дней",
                ]
            },
            "pagination": {"default_page_size": 5, "max_page_size": 50, "query_param": "page_size"},
            "telegram_integration": {
                "bot_username": "@anton_tumashov_bot",
                "commands": [
                    "/start - Начало работы",
                    "/connect {код} - Подключить аккаунт",
                    "/status - Статус подключения",
                    "/stats - Статистика привычек",
                    "/help - Справка по командам",
                ],
            },
        }
    }
    return JsonResponse(spec)
