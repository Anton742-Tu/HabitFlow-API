from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        """Валидация паролей"""
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        """Создание пользователя"""
        # Удаляем password2 из validated_data
        validated_data.pop("password2")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""

    habits_count = serializers.SerializerMethodField()
    public_habits_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "habits_count",
            "public_habits_count",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    def get_habits_count(self, obj):
        """Количество привычек пользователя"""
        return obj.habits.count()

    def get_public_habits_count(self, obj):
        """Количество публичных привычек пользователя"""
        return obj.habits.filter(is_public=True).count()
