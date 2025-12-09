import csv
import json
from datetime import date, datetime, timedelta

from django.db import models
from django.db.models import Count, DurationField, ExpressionWrapper, F
from django.http import HttpResponse
from django.utils import timezone
from django_filters import BooleanFilter, DateFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Habit, HabitCompletion
from .permissions import HabitCompletionPermission
from .serializers import HabitCompletionSerializer, HabitSerializer, PublicHabitSerializer


def filter_has_completions_today(queryset, name, value):
    """Фильтр по наличию выполнений сегодня"""
    today = date.today()

    if value:
        # Привычки, которые были выполнены сегодня
        return queryset.filter(completions__completed_at__date=today).distinct()
    else:
        # Привычки, которые не выполнялись сегодня
        return queryset.exclude(completions__completed_at__date=today).distinct()


def filter_min_completions(queryset, name, value):
    """Фильтр по минимальному количеству выполнений"""
    from django.db.models import Count

    return queryset.annotate(completion_count=Count("completions")).filter(completion_count__gte=value)


def filter_last_completed_before(queryset, name, value):
    """Фильтр по последнему выполнению до указанной даты"""
    return (
        queryset.filter(completions__completed_at__date__lt=value)
        .annotate(last_completion=models.Max("completions__completed_at"))
        .filter(last_completion__isnull=False)
    )


def filter_last_completed_after(queryset, name, value):
    """Фильтр по последнему выполнению после указанной даты"""
    return (
        queryset.filter(completions__completed_at__date__gte=value)
        .annotate(last_completion=models.Max("completions__completed_at"))
        .filter(last_completion__isnull=False)
    )


class HabitFilter(FilterSet):
    """Фильтр для привычек с дополнительными полями"""

    date_from = DateFilter(field_name="created_at", lookup_expr="gte")  # ⬅️ DateFilter из django_filters
    date_to = DateFilter(field_name="created_at", lookup_expr="lte")
    has_completions_today = BooleanFilter(method="filter_has_completions_today")
    min_completions = NumberFilter(method="filter_min_completions")

    class Meta:
        model = Habit
        fields = [
            "is_pleasant",
            "frequency",
            "is_public",
            "date_from",
            "date_to",
            "has_completions_today",
            "min_completions",
        ]

    def filter_has_completions_today(self, queryset, name, value):
        """Фильтр по наличию выполнений сегодня"""
        today = date.today()

        if value:
            # Привычки, которые были выполнены сегодня
            return queryset.filter(completions__completed_at__date=today).distinct()
        else:
            # Привычки, которые не выполнялись сегодня
            return queryset.exclude(completions__completed_at__date=today).distinct()

    def filter_min_completions(self, queryset, name, value):
        """Фильтр по минимальному количеству выполнений"""
        from django.db.models import Count

        return queryset.annotate(completion_count=Count("completions")).filter(completion_count__gte=value)


class StandardPagination(PageNumberPagination):
    """Кастомная пагинация - 5 привычек на страницу"""

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"


class HabitViewSet(viewsets.ModelViewSet):
    """
    Управление привычками пользователя.

    Доступные действия:
    - GET /api/habits/ - список всех привычек (свои + публичные)
    - POST /api/habits/ - создать новую привычку
    - GET /api/habits/{id}/ - получить детали привычки
    - PUT/PATCH /api/habits/{id}/ - обновить привычку
    - DELETE /api/habits/{id}/ - удалить привычку

    Особенности:
    - Только владелец может изменять/удалять привычки
    - Публичные привычки видны всем пользователям (только чтение)
    - Автоматическая валидация по правилам Atomic Habits
    """

    @swagger_auto_schema(
        operation_description="Список привычек с пагинацией и фильтрацией",
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY, description="Номер страницы", type=openapi.TYPE_INTEGER),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Количество элементов на странице (макс. 50)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "is_pleasant", openapi.IN_QUERY, description="Фильтр по типу привычки", type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                "frequency",
                openapi.IN_QUERY,
                description="Фильтр по периодичности",
                type=openapi.TYPE_STRING,
                enum=["daily", "weekly", "monthly"],
            ),
            openapi.Parameter(
                "is_public", openapi.IN_QUERY, description="Фильтр по публичности", type=openapi.TYPE_BOOLEAN
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создание новой привычки",
        request_body=HabitSerializer,
        responses={
            201: openapi.Response(
                description="Привычка создана",
                examples={
                    "application/json": {
                        "id": 1,
                        "user": {"id": 1, "username": "ivan"},
                        "place": "Дом",
                        "time": "08:00",
                        "action": "Пить воду",
                        "is_pleasant": False,
                        "frequency": "daily",
                        "duration": 60,
                        "full_description": "Я буду пить воду в 08:00 в дом",
                    }
                },
            ),
            400: "Ошибка валидации (проверьте правила Atomic Habits)",
        },
    )
    @swagger_auto_schema(
        operation_description="Создание новой привычки",
        request_body=HabitSerializer,
        responses={
            201: openapi.Response(
                description="Привычка создана",
                examples={
                    "application/json": {
                        "id": 1,
                        "user": {"id": 1, "username": "ivan"},
                        "place": "Дом",
                        "time": "08:00",
                        "action": "Пить воду",
                        "is_pleasant": False,
                        "frequency": "daily",
                        "duration": 60,
                        "full_description": "Я буду пить воду в 08:00 в дом",
                    }
                },
            ),
            400: "Ошибка валидации (проверьте правила Atomic Habits)",
        },
    )
    def create(self, request, *args, **kwargs):
        """Создание новой привычки"""
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """
        Возвращает queryset в зависимости от пользователя.

        Правила:
        1. Аутентифицированный пользователь видит:
           - Все свои привычки (полный доступ)
           - Публичные привычки других пользователей (только чтение)
        2. Неаутентифицированный пользователь видит:
           - Только публичные привычки (только чтение)
        """
        user = self.request.user

        if user.is_authenticated:
            # Свои привычки + публичные привычки других пользователей
            return (
                Habit.objects.filter(models.Q(user=user) | models.Q(is_public=True))
                .distinct()
                .select_related("user", "related_habit")
                .prefetch_related("completions")
            )

        # Для неаутентифицированных пользователей - только публичные привычки
        return Habit.objects.filter(is_public=True).select_related("user").prefetch_related("completions")

    def perform_create(self, serializer):
        """При создании привычки автоматически устанавливаем владельца"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        """Отметить выполнение привычки (только для владельца)"""
        habit = self.get_object()

        # Проверяем, что привычка принадлежит пользователю
        if habit.user != request.user:
            return Response(
                {"error": "Вы не можете отмечать выполнение чужих привычек."}, status=status.HTTP_403_FORBIDDEN
            )

        # Проверяем, можно ли выполнять привычку сегодня
        if not habit.can_be_completed_today():
            return Response(
                {"error": "Выполнять эту привычку можно только раз в указанный период."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаем запись о выполнении
        completion_data = {"habit": habit.id, "is_completed": True, "note": request.data.get("note", "")}

        serializer = HabitCompletionSerializer(data=completion_data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def public(self, request):
        """
        Получить только публичные привычки.
        Доступно всем пользователям (включая неаутентифицированных).
        """
        public_habits = Habit.objects.filter(is_public=True).select_related("user")

        # Используем пагинацию
        page = self.paginate_queryset(public_habits)
        if page is not None:
            # Используем PublicHabitSerializer который теперь включает is_public
            serializer = PublicHabitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PublicHabitSerializer(public_habits, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_habits(self, request):
        """
        Получить только свои привычки.
        Только для аутентифицированных пользователей.
        """
        my_habits = Habit.objects.filter(user=request.user).select_related("related_habit")

        # Используем пагинацию
        page = self.paginate_queryset(my_habits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(my_habits, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated])
    def toggle_public(self, request, pk=None):
        """
        Переключить статус публичности привычки.
        Только для владельца.
        """
        habit = self.get_object()

        # Проверяем, что пользователь - владелец
        if habit.user != request.user:
            return Response(
                {"error": "Вы не можете изменять статус публичности чужих привычек."}, status=status.HTTP_403_FORBIDDEN
            )

        # Меняем статус публичности
        habit.is_public = not habit.is_public
        habit.save()

        return Response(
            {
                "id": habit.id,
                "is_public": habit.is_public,
                "message": f'Привычка теперь {"публичная" if habit.is_public else "приватная"}',
            }
        )


def _calculate_completion_stats(user):
    """Рассчет статистики выполнения привычек"""
    habits = Habit.objects.filter(user=user)

    stats = {"total_expected": 0, "total_completed": 0, "by_frequency": {}, "by_habit": []}

    for habit in habits:
        # Рассчитываем ожидаемое количество выполнений
        days_active = (timezone.now() - habit.created_at).days + 1
        expected = days_active / habit.frequency_days

        # Фактическое количество выполнений
        actual = habit.completions.count()

        # Процент выполнения для этой привычки
        percentage = (actual / expected * 100) if expected > 0 else 0

        stats["total_expected"] += expected
        stats["total_completed"] += actual

        # Группировка по частоте
        freq = habit.frequency
        if freq not in stats["by_frequency"]:
            stats["by_frequency"][freq] = {"count": 0, "completed": 0, "percentage": 0}

        stats["by_frequency"][freq]["count"] += 1
        stats["by_frequency"][freq]["completed"] += actual

        # Статистика по конкретной привычке
        stats["by_habit"].append(
            {
                "id": habit.id,
                "action": habit.action,
                "expected": round(expected, 1),
                "actual": actual,
                "percentage": round(percentage, 1),
                "frequency": habit.frequency,
            }
        )

    # Общий процент выполнения
    stats["overall_percentage"] = round(
        (stats["total_completed"] / stats["total_expected"] * 100) if stats["total_expected"] > 0 else 0, 1
    )

    # Рассчет процентов для групп по частоте
    for freq in stats["by_frequency"]:
        freq_stats = stats["by_frequency"][freq]
        freq_stats["percentage"] = round(
            (freq_stats["completed"] / (freq_stats["count"] * 30) * 100) if freq_stats["count"] > 0 else 0, 1
        )

    return stats


def _calculate_current_streak(user):
    """Рассчет текущей серии последовательных дней с выполнением привычек"""
    # Получаем все выполнения за последние 30 дней
    month_ago = timezone.now() - timedelta(days=30)

    completion_dates = (
        HabitCompletion.objects.filter(habit__user=user, completed_at__gte=month_ago)
        .dates("completed_at", "day")
        .order_by("-completed_at")
    )

    if not completion_dates:
        return 0

    # Находим самую длинную последовательность дней подряд
    streak = 1
    current_date = completion_dates[0]

    for i in range(1, len(completion_dates)):
        prev_date = completion_dates[i]
        days_diff = (current_date - prev_date).days

        if days_diff == 1:
            streak += 1
            current_date = prev_date
        else:
            break

    return streak


def _calculate_habit_streak(habit):
    """Рассчет текущей серии выполнения конкретной привычки"""
    completions = habit.completions.order_by("-completed_at")

    if not completions.exists():
        return 0

    streak = 0
    current_date = completions.first().completed_at.date()

    for completion in completions:
        completion_date = completion.completed_at.date()

        if completion_date == current_date:
            continue

        days_diff = (current_date - completion_date).days

        if days_diff == 1:
            streak += 1
            current_date = completion_date
        else:
            break

    return streak + 1  # +1 для дня первого выполнения


def _export_to_csv(habits, user):
    """Экспорт в CSV формат"""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="habits_{user.username}_{datetime.now().date()}.csv"'

    writer = csv.writer(response)

    # Заголовки
    writer.writerow(
        [
            "ID",
            "Действие",
            "Место",
            "Время",
            "Периодичность",
            "Длительность (сек)",
            "Приятная привычка",
            "Вознаграждение",
            "Связанная привычка",
            "Публичная",
            "Создано",
            "Выполнений",
        ]
    )

    # Данные
    for habit in habits:
        writer.writerow(
            [
                habit.id,
                habit.action,
                habit.place,
                habit.time.strftime("%H:%M") if habit.time else "",
                habit.frequency,
                habit.duration,
                "Да" if habit.is_pleasant else "Нет",
                habit.reward or "",
                habit.related_habit.action if habit.related_habit else "",
                "Да" if habit.is_public else "Нет",
                habit.created_at.strftime("%Y-%m-%d %H:%M"),
                habit.completions.count(),
            ]
        )

    return response


def _export_to_json(habits, user):
    """Экспорт в JSON формат"""
    data = {
        "export_date": datetime.now().isoformat(),
        "user": {
            "username": user.username,
            "email": user.email,
        },
        "habits": [],
    }

    for habit in habits:
        habit_data = {
            "id": habit.id,
            "action": habit.action,
            "place": habit.place,
            "time": habit.time.strftime("%H:%M") if habit.time else None,
            "frequency": habit.frequency,
            "duration_seconds": habit.duration,
            "is_pleasant": habit.is_pleasant,
            "reward": habit.reward,
            "related_habit_id": habit.related_habit_id,
            "is_public": habit.is_public,
            "created_at": habit.created_at.isoformat(),
            "updated_at": habit.updated_at.isoformat(),
            "full_description": habit.full_description,
            "completions": [],
        }

        # Добавляем последние 30 выполнений
        recent_completions = habit.completions.order_by("-completed_at")[:30]
        for completion in recent_completions:
            habit_data["completions"].append(
                {
                    "completed_at": completion.completed_at.isoformat(),
                    "is_completed": completion.is_completed,
                    "note": completion.note,
                }
            )

        data["habits"].append(habit_data)

    response = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="habits_{user.username}_{datetime.now().date()}.json"'

    return response


class HabitCompletionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления выполнениями привычек.

    Права доступа:
    - Только владелец привычки может создавать/просматривать/удалять выполнения
    """

    queryset = HabitCompletion.objects.all()
    serializer_class = HabitCompletionSerializer
    permission_classes = [HabitCompletionPermission]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    ordering_fields = ["completed_at"]
    ordering = ["-completed_at"]

    def get_queryset(self):
        """
        Пользователь видит только выполнения своих привычек.
        """
        if self.request.user.is_authenticated:
            return HabitCompletion.objects.filter(habit__user=self.request.user).select_related("habit")

        return HabitCompletion.objects.none()

    def perform_create(self, serializer):
        """При создании проверяем, что привычка принадлежит пользователю"""
        habit = serializer.validated_data["habit"]

        if habit.user != self.request.user:
            raise serializers.ValidationError("Вы можете добавлять выполнения только для своих привычек.")

        # Проверяем периодичность выполнения
        if not habit.can_be_completed_today():
            raise serializers.ValidationError(f"Привычку можно выполнять раз в {habit.frequency_days} дней.")

        serializer.save()

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request):
        """Статистика выполнения привычек пользователя"""
        user = request.user

        # Базовые метрики
        total_habits = Habit.objects.filter(user=user).count()
        pleasant_habits = Habit.objects.filter(user=user, is_pleasant=True).count()
        useful_habits = Habit.objects.filter(user=user, is_pleasant=False).count()

        # Выполнения сегодня
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        completions_today = HabitCompletion.objects.filter(
            habit__user=user, completed_at__range=[today_start, today_end]
        ).count()

        # Статистика за неделю
        week_ago = timezone.now() - timedelta(days=7)

        weekly_completions = (
            HabitCompletion.objects.filter(habit__user=user, completed_at__gte=week_ago)
            .values("completed_at__date")
            .annotate(count=Count("id"))
            .order_by("completed_at__date")
        )

        # Процент выполнения привычек
        completion_stats = _calculate_completion_stats(user)

        # Самые успешные привычки
        successful_habits = (
            Habit.objects.filter(user=user)
            .annotate(
                completion_count=Count("completions"), last_completion_date=models.Max("completions__completed_at")
            )
            .order_by("-completion_count")[:5]
        )

        successful_habits_data = [
            {
                "id": habit.id,
                "action": habit.action,
                "completion_count": habit.completion_count,
                "last_completed": habit.last_completion_date,
            }
            for habit in successful_habits
        ]

        # Привычки, требующие внимания (не выполнялись более 3 дней)
        attention_needed = (
            Habit.objects.filter(user=user, completions__isnull=False)
            .annotate(
                last_completion=models.Max("completions__completed_at"),
                days_since_last=ExpressionWrapper(timezone.now() - F("last_completion"), output_field=DurationField()),
            )
            .filter(days_since_last__gt=timedelta(days=3))
            .values("id", "action", "last_completion")[:5]
        )

        return Response(
            {
                "summary": {
                    "total_habits": total_habits,
                    "pleasant_habits": pleasant_habits,
                    "useful_habits": useful_habits,
                    "completions_today": completions_today,
                },
                "completion_rate": completion_stats,
                "weekly_completions": list(weekly_completions),
                "successful_habits": successful_habits_data,
                "attention_needed": list(attention_needed),
                "current_streak": _calculate_current_streak(user),
            }
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def progress(self, request, pk=None):
        """Прогресс выполнения конкретной привычки"""
        habit = self.get_object()

        # Проверяем права доступа
        if habit.user != request.user and not habit.is_public:
            return Response({"error": "У вас нет доступа к прогрессу этой привычки"}, status=status.HTTP_403_FORBIDDEN)

        # Базовые метрики
        total_completions = habit.completions.count()

        # За последние 30 дней
        month_ago = timezone.now() - timedelta(days=30)
        recent_completions = habit.completions.filter(completed_at__gte=month_ago).count()

        # Рассчет процента выполнения
        expected_completions = 30 / habit.frequency_days
        completion_percentage = (recent_completions / expected_completions * 100) if expected_completions > 0 else 0

        # Текущая серия (streak)
        current_streak = _calculate_habit_streak(habit)

        # График выполнения за неделю
        week_ago = timezone.now() - timedelta(days=7)

        weekly_completions = (
            habit.completions.filter(completed_at__gte=week_ago)
            .values("completed_at__date")
            .annotate(count=Count("id"))
            .order_by("completed_at__date")
        )

        # Время суток, когда чаще всего выполняется
        completion_times = habit.completions.values_list("completed_at__hour", flat=True)

        # Медиана времени выполнения
        times_list = list(completion_times)
        if times_list:
            times_list.sort()
            median_time = times_list[len(times_list) // 2]
        else:
            median_time = None

        return Response(
            {
                "habit": {
                    "id": habit.id,
                    "action": habit.action,
                    "frequency": habit.frequency,
                },
                "completions": {
                    "total": total_completions,
                    "recent_30_days": recent_completions,
                    "percentage": round(completion_percentage, 1),
                    "expected": round(expected_completions, 1),
                },
                "streak": {
                    "current": current_streak,
                    "longest": self._calculate_longest_streak(habit),
                },
                "weekly_data": list(weekly_completions),
                "time_analysis": {
                    "median_hour": median_time,
                    "scheduled_time": habit.time.hour if habit.time else None,
                },
                "next_expected": self._calculate_next_expected_date(habit),
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def export(self, request):
        """Экспорт привычек в различных форматах"""
        format_type = request.query_params.get("format", "json")
        user = request.user

        habits = Habit.objects.filter(user=user).select_related("related_habit")

        if format_type == "csv":
            return _export_to_csv(habits, user)
        elif format_type == "json":
            return _export_to_json(habits, user)
        else:
            return Response({"error": "Unsupported format. Use csv or json."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def bulk_complete(self, request):
        """Массовое выполнение нескольких привычек"""
        habit_ids = request.data.get("habit_ids", [])
        note = request.data.get("note", "")

        if not habit_ids:
            return Response({"error": "No habit_ids provided"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        successes = []
        errors = []

        for habit_id in habit_ids:
            try:
                habit = Habit.objects.get(id=habit_id, user=user)

                # Проверяем, можно ли выполнять привычку
                if not habit.can_be_completed_today():
                    errors.append(
                        {
                            "habit_id": habit_id,
                            "error": f"Cannot complete habit more frequently than {habit.frequency_days} days",
                        }
                    )
                    continue

                # Создаем выполнение
                completion = HabitCompletion.objects.create(habit=habit, is_completed=True, note=note)

                successes.append(
                    {
                        "habit_id": habit_id,
                        "action": habit.action,
                        "completion_id": completion.id,
                        "completed_at": completion.completed_at,
                    }
                )

            except Habit.DoesNotExist:
                errors.append({"habit_id": habit_id, "error": "Habit not found or access denied"})
            except Exception as e:
                errors.append({"habit_id": habit_id, "error": str(e)})

        return Response(
            {
                "successes": successes,
                "errors": errors,
                "summary": {"total": len(habit_ids), "successful": len(successes), "failed": len(errors)},
            }
        )

    @action(detail=False, methods=["patch"], permission_classes=[permissions.IsAuthenticated])
    def bulk_update_public(self, request):
        """Массовое обновление статуса публичности"""
        habit_ids = request.data.get("habit_ids", [])
        is_public = request.data.get("is_public")

        if is_public is None:
            return Response({"error": "is_public field is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        updated_count = 0

        # Проверяем, что все привычки принадлежат пользователю
        habits = Habit.objects.filter(id__in=habit_ids, user=user)

        if habits.count() != len(habit_ids):
            return Response({"error": "Some habits not found or access denied"}, status=status.HTTP_400_BAD_REQUEST)

        # Массовое обновление
        updated_count = habits.update(is_public=is_public)

        return Response(
            {
                "updated_count": updated_count,
                "is_public": is_public,
                "message": f"Successfully updated {updated_count} habits",
            }
        )
