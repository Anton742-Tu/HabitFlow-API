from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Habit, HabitCompletion

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя (только для чтения)"""

    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class HabitCompletionSerializer(serializers.ModelSerializer):
    """Сериализатор для отметки выполнения привычки"""

    class Meta:
        model = HabitCompletion
        fields = ["id", "habit", "completed_at", "is_completed", "note"]
        read_only_fields = ["id", "completed_at"]

    def validate(self, data):
        """Валидация данных выполнения привычки"""
        habit = data.get("habit")

        # Проверяем, что привычка принадлежит текущему пользователю
        request = self.context.get("request")
        if request and habit.user != request.user:
            raise serializers.ValidationError("Вы можете отмечать выполнение только своих привычек.")

        return data


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для привычки"""

    user = UserSerializer(read_only=True)
    related_habit = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.filter(is_pleasant=True), required=False, allow_null=True
    )
    completions = HabitCompletionSerializer(many=True, read_only=True)
    full_description = serializers.SerializerMethodField()  # И здесь тоже исправляем

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "place",
            "time",
            "action",
            "is_pleasant",
            "related_habit",
            "frequency",
            "reward",
            "duration",
            "is_public",
            "created_at",
            "updated_at",
            "completions",
            "full_description",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_full_description(self, obj):
        """Метод для получения full_description из модели"""
        return obj.full_description

    def validate(self, data):
        """Валидация данных привычки"""
        request = self.context.get("request")

        # Проверяем, что для приятной привычки не указаны reward или related_habit
        is_pleasant = data.get("is_pleasant", self.instance.is_pleasant if self.instance else False)

        if is_pleasant:
            if data.get("reward"):
                raise serializers.ValidationError("У приятной привычки не может быть вознаграждения.")
            if data.get("related_habit"):
                raise serializers.ValidationError("У приятной привычки не может быть связанной привычки.")

        # Проверяем, что не указаны одновременно reward и related_habit
        if data.get("reward") and data.get("related_habit"):
            raise serializers.ValidationError("Нельзя одновременно указывать и связанную привычку и вознаграждение.")

        return data

    def create(self, validated_data):
        """Создание привычки с привязкой к текущему пользователю"""
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)


class PublicHabitSerializer(serializers.ModelSerializer):
    """Сериализатор для публичных привычек (ограниченные поля)"""

    user = UserSerializer(read_only=True)
    full_description = serializers.SerializerMethodField()  # Используем SerializerMethodField

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "place",
            "time",
            "action",
            "frequency",
            "duration",
            "created_at",
            "full_description",
            "is_public",
        ]
        read_only_fields = fields

    def get_full_description(self, obj):
        """Метод для получения full_description из модели"""
        return obj.full_description
