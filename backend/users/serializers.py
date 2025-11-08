from django.contrib.auth import get_user_model

from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserUserSerializer

from api.fields import Base64ImageField
from users.models import Subscription
from recipes.models import Recipe

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


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для вывода рецептов в подписках."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами и количеством рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = UserSerializer.Meta.read_only_fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, user):
        """Список рецептов пользователя."""
        request = self.context.get('request')
        recipes_qs = user.recipes.all()

        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        try:
            if recipes_limit is not None:
                recipes_qs = recipes_qs[:int(recipes_limit)]
        except (ValueError, TypeError):
            pass

        return RecipeShortSerializer(
            recipes_qs, many=True, context={'request': request}
        ).data


class SubscriptionListSerializer(UserWithRecipesSerializer):
    """Сериализатор для подписок текущего пользователя."""
    is_subscribed = serializers.SerializerMethodField()
