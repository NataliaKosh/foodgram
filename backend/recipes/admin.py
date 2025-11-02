from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Subscription,
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'is_staff'
    )
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'created')
    list_filter = ('created',)
    search_fields = (
        'user__email', 'user__username', 'author__email', 'author__username'
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


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
    list_filter = ('tags', 'author', 'created')
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
