from collections import Counter

from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    Subscription,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)
from .fields import Base64ImageField


User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = [*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar']
        read_only_fields = fields

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
        max_size = settings.FOODGRAM['MAX_AVATAR_SIZE']
        if avatar and hasattr(avatar, 'size') and avatar.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise serializers.ValidationError(
                f'Размер файла не должен превышать {max_mb:.1f} MB'
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
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами и количеством рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, 'recipes', 'recipes_count']
        read_only_fields = fields

    def get_recipes(self, user):
        """Список рецептов пользователя."""
        request = self.context.get('request')
        recipes = user.recipes.all()

        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        try:
            if recipes_limit is not None:
                recipes = recipes[:int(recipes_limit)]
        except (ValueError, TypeError):
            pass

        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data


def validate_unique_items(items, field_name):
    """Проверка наличия и уникальности элементов списка."""
    if not items:
        raise serializers.ValidationError(
            f'Добавьте хотя бы один {field_name}'
        )

    item_ids = [
        (
            item.get('id')
            if isinstance(item, dict)
            else getattr(item, 'id', item)
        )
        for item in items
    ]

    duplicates = [
        item_id for item_id, count
        in Counter(item_ids).items()
        if count > 1
    ]

    if duplicates:
        msg = (
            f'{field_name.capitalize()} не должны повторяться: '
            f'{duplicates}'
        )
        raise serializers.ValidationError(msg)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = fields


class IngredientInRecipeCreateSerializer(serializers.Serializer):
    """Сериализатор ингредиентов при создании/обновлении рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]
        read_only_fields = fields

    def _check_user_related(self, obj, model_cls):
        """Проверяет, добавлен ли рецепт в избранное или в корзину покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return model_cls.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_favorited(self, recipe):
        """Проверяет, находится ли рецепт в избранном."""
        return self._check_user_related(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        """Проверяет, находится ли рецепт в корзине."""
        return self._check_user_related(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов"""
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME)],
        help_text="Время приготовления в минутах"
    )

    class Meta:
        model = Recipe
        fields = ['id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time']

    @staticmethod
    def _set_ingredients(recipe, ingredients_data):
        """Меняет ингредиенты для рецепта, удаляя старые"""
        recipe.recipe_ingredients.all().delete()

        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=data['id'],
                amount=data['amount']
            ) for data in ingredients_data
        )

    def validate_ingredients(self, ingredients):
        validate_unique_items(ingredients, 'ингредиент')
        return ingredients

    def validate_tags(self, tags):
        validate_unique_items(tags, 'тег')
        return tags

    def create(self, validated_data):
        """Создает новый рецепт с тегами и ингредиентами"""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)

        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт и его ингредиенты/теги"""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance.tags.set(tags_data)
        self._set_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает сериализованные данные через RecipeSerializer"""
        return RecipeSerializer(
            instance, context=self.context
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимального представления рецепта"""
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = fields
