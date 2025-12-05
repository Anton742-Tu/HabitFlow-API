from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Habit, HabitCompletion
from .permissions import IsOwnerOrPublicReadOnly
from .serializers import HabitCompletionSerializer, HabitSerializer, PublicHabitSerializer


class StandardPagination(PageNumberPagination):
    """Кастомная пагинация - 5 привычек на страницу"""

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"


class HabitViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления привычками.

    Пользователь видит только свои привычки и публичные привычки других пользователей.
    Пагинация: 5 привычек на страницу.
    """

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPublicReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_pleasant", "frequency", "is_public"]
    search_fields = ["action", "place", "reward"]
    ordering_fields = ["time", "created_at", "updated_at"]
    ordering = ["time"]

    def get_queryset(self):
        """
        Возвращает queryset в зависимости от пользователя.
        Пользователь видит:
        1. Все свои привычки
        2. Публичные привычки других пользователей
        """
        user = self.request.user

        if user.is_authenticated:
            # Свои привычки + публичные привычки других пользователей
            return (
                Habit.objects.filter(models.Q(user=user) | models.Q(is_public=True))
                .distinct()
                .select_related("user", "related_habit")
            )

        # Для неаутентифицированных пользователей - только публичные привычки
        return Habit.objects.filter(is_public=True).select_related("user")

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Отметить выполнение привычки"""
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
        """Получить только публичные привычки (без пагинации или с другой пагинацией)"""
        public_habits = Habit.objects.filter(is_public=True).select_related("user")

        # Используем ту же пагинацию, но можно настроить отдельно
        page = self.paginate_queryset(public_habits)
        if page is not None:
            serializer = PublicHabitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PublicHabitSerializer(public_habits, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_habits(self, request):
        """Получить только свои привычки"""
        my_habits = Habit.objects.filter(user=request.user).select_related("related_habit")

        # Используем пагинацию
        page = self.paginate_queryset(my_habits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(my_habits, many=True)
        return Response(serializer.data)


class HabitCompletionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления выполнениями привычек"""

    queryset = HabitCompletion.objects.all()
    serializer_class = HabitCompletionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Пользователь видит только выполнения своих привычек"""
        return HabitCompletion.objects.filter(habit__user=self.request.user).select_related("habit")

    def perform_create(self, serializer):
        """При создании проверяем, что привычка принадлежит пользователю"""
        habit = serializer.validated_data["habit"]

        if habit.user != self.request.user:
            raise serializers.ValidationError("Вы можете добавлять выполнения только для своих привычек.")

        # Проверяем периодичность выполнения
        if not habit.can_be_completed_today():
            raise serializers.ValidationError(f"Привычку можно выполнять раз в {habit.frequency_days} дней.")

        serializer.save()
