from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
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
    """Регистрация нового пользователя"""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {"id": user.id, "username": user.username, "email": user.email},
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Профиль пользователя"""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Выход из системы (blacklist refresh token)"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
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
