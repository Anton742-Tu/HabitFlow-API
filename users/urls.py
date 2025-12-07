from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CustomTokenObtainPairView, LogoutView, RegisterView, UserProfileView, generate_telegram_code

urlpatterns = [
    # Аутентификация
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Профиль
    path("profile/", UserProfileView.as_view(), name="profile"),
    # Telegram подключение
    path("telegram/connect/", generate_telegram_code, name="telegram-connect"),
]
