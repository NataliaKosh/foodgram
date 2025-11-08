from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from api.fields import Base64ImageField
from users.models import Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        read_only_fields = (
            DjoserUserSerializer.Meta.read_only_fields + ('is_subscribed',)
        )

    def get_is_subscribed(self, author):
        """Проверят подписан ли ползьватель на данного автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=author
            ).exists()
        return False


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']

    def validate_avatar(self, avatar):
        """Проверяет размер загружаемого аватара."""
        if (
            avatar and hasattr(avatar, 'size')
            and avatar.size > 2 * 1024 * 1024
        ):
            raise serializers.ValidationError(
                'Размер файла не должен превышать 2MB'
            )
        return avatar

    def update(self, instance, validated_data):
        """Сохраняет новый аватар."""
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами и количеством рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = (
            UserSerializer.Meta.read_only_fields + ('recipes', 'recipes_count')
        )

    def get_recipes(self, obj):
        """Список рецептов."""
        request = self.context.get('request')
        recipes = obj.recipes.all()

        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": (
                    request.build_absolute_uri(recipe.image.url)
                    if request else recipe.image.url
                ),
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        """Количество рецептов."""
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор информации о подписке на пользователя."""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        """Возвращает True, если есть подписка."""
        return True

    def get_avatar(self, obj):
        """Возвращает URL аватара автора подписки, если есть подписка."""
        if obj.author.avatar:
            request = self.context.get('request')
            return (
                request.build_absolute_uri(obj.author.avatar.url)
                if request else obj.author.avatar.url
            )
        return None

    def get_recipes(self, obj):
        """Возвращает список рецептов автора подписки."""
        request = self.context.get('request')
        recipes = obj.author.recipes.all()

        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": (
                    request.build_absolute_uri(recipe.image.url)
                    if request else recipe.image.url
                ),
                "cooking_time": recipe.cooking_time
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора подписки."""
        return obj.author.recipes.count()


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя"""
    new_password = serializers.CharField(
        required=True, validators=[validate_password]
    )
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Проверяет корректность текущего пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def save(self, **kwargs):
        """Сохраняет новый пароль"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
