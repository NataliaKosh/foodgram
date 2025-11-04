from django.core.validators import MinValueValidator

from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.serializers import UserSerializer
from .fields import Base64ImageField


MIN_COOKING_TIME = 1
MIN_INGREDIENT_AMOUNT = 1
MIN_RECIPE_FIELDS = ['id', 'name', 'image', 'cooking_time']
RECIPE_FIELDS = [
    'id', 'tags', 'author', 'ingredients', 'is_favorited',
    'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
]


def validate_unique_items(items, field_name):
    """Проверка наличия и уникальности элементов списка."""
    if not items:
        raise serializers.ValidationError(
            f'Добавьте хотя бы один {field_name}'
        )

    seen_ids = set()
    duplicates = []
    for item in items:
        item_id = item.get('id') if isinstance(item, dict) else getattr(item, 'id', item)
        if item_id in seen_ids:
            duplicates.append(item_id)
        seen_ids.add(item_id)

    if duplicates:
        raise serializers.ValidationError(
            f'{field_name.capitalize()} не должны повторяться: {duplicates}'
        )

    return items

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
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = ['id', 'name', 'measurement_unit', 'amount']


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
        fields = RECIPE_FIELDS
        read_only_fields = [RECIPE_FIELDS[0]]

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
    """Сериализатор для создани и обновления рецептов"""
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['image'].required = False

    @staticmethod
    def _set_ingredients(recipe, ingredients_data):
        """Меняет ингредиенты для рецепта, удаляя старые"""
        recipe.recipe_ingredients.delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=data['id'],
                amount=data['amount']
            ) for data in ingredients_data
        )

    def validate_ingredients(self, ingredients):
        """Проверяет наличие и уникальность ингредиентов"""
        return validate_unique_items(ingredients, 'ингредиент')

    def validate_tags(self, tags):
        """Проверяет наличие и уникальность тегов"""
        return validate_unique_items(tags, 'тег')

    def create(self, validated_data):
        """Создает новый рецепт с тегами и ингредиентами"""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт и его ингредиенты/теги"""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)
        self._set_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращает сериализованные данные через RecipeSerializer"""
        return RecipeSerializer(
            instance, context=self.context
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимального представления рецепта"""
    class Meta:
        model = Recipe
        fields = MIN_RECIPE_FIELDS
        read_only_fields = [MIN_RECIPE_FIELDS[0]]
