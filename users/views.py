from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserProfileSerializer, UserRegisterSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT токенов"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавляем кастомные поля в токен
        token["username"] = user.username
        token["email"] = user.email
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомный view для получения JWT токенов"""

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.

    После успешной регистрации автоматически возвращаются JWT токены.
    """

    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Пользователь создан",
                examples={
                    "application/json": {
                        "user": {"id": 1, "username": "ivan", "email": "ivan@example.com"},
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    }
                },
            ),
            400: "Ошибка валидации данных",
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserRegisterSerializer(user, context=self.get_serializer_context()).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получение профиля пользователя"""
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        """Обновление профиля пользователя"""
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Выход из системы (blacklist refresh token)"""

    permission_classes = [permissions.IsAuthenticated]


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    operation_description="""
    Генерация уникального кода для подключения Telegram бота.

    Код действителен 10 минут. Для подключения:
    1. Найдите в Telegram бота @anton_tumashov_bot
    2. Отправьте команду /start
    3. Отправьте команду: /connect {ваш_код}
    """,
    responses={
        200: openapi.Response(
            description="Код сгенерирован",
            examples={
                "application/json": {
                    "code": "abc123xyz",
                    "bot_username": "anton_tumashov_bot",
                    "instructions": [
                        "1. Найдите в Telegram бота @anton_tumashov_bot",
                        "2. Отправьте команду /start",
                        "3. Отправьте команду: /connect abc123xyz",
                    ],
                }
            },
        )
    },
)
def generate_telegram_code(request):
    """Генерация кода для подключения Telegram"""
    from telegram_bot.models import TelegramConnectionCode

    user = request.user

    # Генерируем новый код
    connection_code = TelegramConnectionCode.generate_code(user)

    return Response(
        {
            "success": True,
            "code": connection_code.code,
            "bot_username": "anton_tumashov_bot",
            "instructions": [
                "1. Найдите в Telegram бота @anton_tumashov_bot",
                "2. Отправьте команду /start",
                "3. Отправьте команду: /connect " + connection_code.code,
                "4. Готово! Вы будете получать уведомления",
            ],
            "expires_at": connection_code.expires_at.isoformat(),
            "expires_in_minutes": 10,
            "user": {"username": user.username, "email": user.email},
        }
    )
