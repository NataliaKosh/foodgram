from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from users.models import User


class Tag(models.Model):
    """Модель тегов рецептов"""
    name = models.CharField(
        max_length=32,
        verbose_name='Название',
        unique=True
    )
    slug_validator = RegexValidator(
        regex=r'^[-a-zA-Z0-9_]+\Z',
        message='Slug может содержать только латинские буквы, цифры, дефисы и подчеркивания'
    )
    slug = models.SlugField(
        max_length=32,
        verbose_name='Уникальный слаг',
        unique=True,
        validators=[slug_validator]
    )
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )
    
    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
    
    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        related_name='recipes',
        through='RecipeIngredient'
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created']
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})


class RecipeIngredient(models.Model):
    """Модель для связи рецепта и ингредиента"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    
    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
    
    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class Favorite(models.Model):
    """Модель избранных рецептов"""
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='favorites',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='favorites',
        on_delete=models.CASCADE
    )
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
    
    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
    
    def __str__(self):
        return f'{self.user} - {self.recipe}'
