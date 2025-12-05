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
