from rest_framework import permissions


class IsOwnerOrPublicReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее:
    - Владельцу: полный доступ (CRUD)
    - Остальным: только чтение публичных привычек
    - Неаутентифицированным: только чтение публичных привычек
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение (GET, HEAD, OPTIONS) для публичных привычек
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user

        # Для остальных методов разрешаем только владельцу
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """Разрешение только для владельца объекта"""

    def has_object_permission(self, request, view, obj):
        # Для привычек
        if hasattr(obj, "user"):
            return obj.user == request.user

        # Для выполнений привычек
        if hasattr(obj, "habit"):
            return obj.habit.user == request.user

        return False


class IsHabitOwner(permissions.BasePermission):
    """
    Разрешение только для владельца привычки.
    Позволяет полный CRUD доступ.
    """

    def has_object_permission(self, request, view, obj):
        # Проверяем, что пользователь - владелец привычки
        return obj.user == request.user


class CanViewPublicHabits(permissions.BasePermission):
    """
    Разрешение на просмотр публичных привычек.
    Позволяет только безопасные методы (GET, HEAD, OPTIONS).
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем только безопасные методы
        if request.method not in permissions.SAFE_METHODS:
            return False

        # Разрешаем просмотр, если привычка публичная ИЛИ пользователь - владелец
        return obj.is_public or obj.user == request.user


class HabitPermission(permissions.BasePermission):
    """
    Комплексное разрешение для привычек:
    - Владелец: полный CRUD доступ
    - Другие пользователи: только чтение публичных привычек
    - Неаутентифицированные: только чтение публичных привычек
    """

    def has_permission(self, request, view):
        # Для создания привычки - нужно быть аутентифицированным
        if request.method == "POST":
            return request.user.is_authenticated

        # Для списка - разрешаем всем (фильтрация в get_queryset)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для остальных методов - нужно быть аутентифицированным
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы для публичных привычек ИЛИ владельца
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user

        # Для изменения/удаления - только владелец
        return obj.user == request.user


class HabitCompletionPermission(permissions.BasePermission):
    """Разрешение для выполнений привычек"""

    def has_permission(self, request, view):
        # Нужна аутентификация для всех операций
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Только владелец привычки может управлять ее выполнениями
        return obj.habit.user == request.user
