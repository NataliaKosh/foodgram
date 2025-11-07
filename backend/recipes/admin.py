from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.utils.safestring import mark_safe
from django.db.models import Count

from .admin_filters import UsedInRecipesFilter, TagUsedInRecipesFilter
from users.models import User, Subscription
from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_preview",
        "recipes_count",
        "subscriptions_count",
        "followers_count",
        "is_staff",
    )
    list_filter = (
        "is_staff",
        "is_active",
        ("recipes", admin.EmptyFieldListFilter),
        ("subscribed", admin.EmptyFieldListFilter),
        ("subscriber", admin.EmptyFieldListFilter),
    )
    search_fields = ("username", "email")
    ordering = ("id",)

    def get_queryset(self, request):
        """Оптимизируем запрос — добавляем аннотации для подсчётов"""
        queryset = (
            super()
            .get_queryset(request)
            .annotate(
                _recipes_count=Count("recipes", distinct=True),
                _subscriptions_count=Count("subscribed", distinct=True),
                _followers_count=Count("subscriber", distinct=True),
            )
        )
        return queryset

    @staticmethod
    @mark_safe
    def avatar_preview(obj):
        """Превью аватара в списке пользователей"""
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}" width="50" height="50" '
                'style="border-radius: 50%;">'
            )
        return "—"

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = "ФИО"

    def recipes_count(self, obj):
        return obj._recipes_count
    recipes_count.short_description = "Рецептов"

    def subscriptions_count(self, obj):
        return obj._subscriptions_count
    subscriptions_count.short_description = "Подписок"

    def followers_count(self, obj):
        return obj._followers_count
    followers_count.short_description = "Подписчиков"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'created')
    list_filter = ('created',)
    search_fields = (
        'user__email', 'user__username', 'author__email', 'author__username'
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "recipes_count")
    search_fields = ("name", "slug")
    list_filter = (TagUsedInRecipesFilter,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(recipe_count=Count("recipes", distinct=True))

    def recipes_count(self, obj):
        return obj.recipe_count
    recipes_count.short_description = "Рецептов"
    recipes_count.admin_order_field = "recipe_count"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit", "recipes_count")
    search_fields = ("name", "measurement_unit", "slug")
    list_filter = ("measurement_unit", UsedInRecipesFilter)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_recipes_count=Count("recipes", distinct=True))

    def recipes_count(self, obj):
        return getattr(obj, "_recipes_count", obj.recipes.count())

    recipes_count.short_description = "Рецептов"
    recipes_count.admin_order_field = "_recipes_count"


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'get_favorites_count',
        'get_in_shopping_carts_count', 'cooking_time', 'created'
    )
    list_filter = (
        ('tags', RelatedOnlyFieldListFilter),
        'author',
        'created'
    )
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)

    def get_favorites_count(self, obj):
        return obj.favorites.count()
    get_favorites_count.short_description = 'В избранном'

    def get_in_shopping_carts_count(self, obj):
        return obj.shopping_cart.count()
    get_in_shopping_carts_count.short_description = 'В корзинах'

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'author', 'image', 'text', 'cooking_time')
        }),
        ('Теги', {
            'fields': ('tags',)
        }),
        ('Статистика', {
            'fields': (
                'get_favorites_count_display',
                'get_in_shopping_carts_count_display'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_favorites_count_display(self, obj):
        return f'{self.get_favorites_count(obj)} раз(а)'
    get_favorites_count_display.short_description = (
        'Число добавлений в избранное'
    )

    def get_in_shopping_carts_count_display(self, obj):
        return f'{self.get_in_shopping_carts_count(obj)} раз(а)'
    get_in_shopping_carts_count_display.short_description = (
        'Число добавлений в корзины покупок'
    )

    readonly_fields = (
        'get_favorites_count_display', 'get_in_shopping_carts_count_display'
    )


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'get_user_email')
    list_filter = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email пользователя'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'get_user_email')
    list_filter = ('user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email пользователя'
