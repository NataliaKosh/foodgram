from django.core.validators import MinValueValidator
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Tag
)
from users.serializers import UserSerializer

from .fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']
        read_only_fields = ['id']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class IngredientInRecipeCreateSerializer(serializers.Serializer):
    """Сериализатор ингредиентов при создании/обновлении рецепта"""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id']


class RecipeListSerializer(serializers.ModelSerializer):
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
        read_only_fields = ['id']

    def _check_user_related(self, obj, model_cls):
        """Проверяет, добавлен ли рецепт в избранное или в корзину покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return model_cls.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном."""
        return self._check_user_related(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в корзине."""
        return self._check_user_related(obj, ShoppingCart)


class BaseRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создани и обновления рецептов"""
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time']
        read_only_fields = ['id']

    @staticmethod
    def _set_ingredients(recipe, ingredients_data):
        """Меняет ингредиенты для рецепта, удаляя старые"""
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=data['id'],
                amount=data['amount']
            ) for data in ingredients_data
        ])

    def validate_ingredients(self, value):
        """Проверяет наличие, уникальность и существование ингредиентов"""
        if not value:
            raise serializers.ValidationError("Добавьте хотя бы один ингредиент")

        unique_ids = {item['id'] for item in value}
        if len(value) != len(unique_ids):
            raise serializers.ValidationError("Ингредиенты не должны повторяться")

        if Ingredient.objects.filter(id__in=unique_ids).count() != len(unique_ids):
            raise serializers.ValidationError("Некоторые ингредиенты не найдены")

        return value

    def validate_tags(self, value):
        """Проверяет наличие и существование тегов"""
        if not value:
            raise serializers.ValidationError("Добавьте хотя бы один тег")

        if Tag.objects.filter(id__in=value).count() != len(value):
            raise serializers.ValidationError("Некоторые теги не найдены")

        return value

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

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.tags.set(tags_data)
        self._set_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Короткий формат рецепта с основными полями, как в RecipeListSerializer"""
        return RecipeListSerializer(instance, context=self.context).data


class RecipeCreateSerializer(BaseRecipeWriteSerializer):
    """Сериализатор для создания рецепта с обязательным изображением"""
    image = Base64ImageField(required=True)


class RecipeUpdateSerializer(BaseRecipeWriteSerializer):
    """Сериализатор для обновления рецепта с необязательным изображением"""
    image = Base64ImageField(required=False)

    def validate(self, data):
        """Проверяет наличие обязательных полей ingredients и tags при обновлении"""
        if 'ingredients' not in data:
            raise serializers.ValidationError({
                'ingredients': ['Это поле обязательно.']
            })
        if 'tags' not in data:
            raise serializers.ValidationError({
                'tags': ['Это поле обязательно.']
            })
        return super().validate(data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимального представления рецепта"""
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ['id']
