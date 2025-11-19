from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.utils.safestring import mark_safe
from django.db.models import Count
from django import forms

from .admin_filters import (
    UsedInRecipesFilter,
    TagUsedInRecipesFilter,
    CookingTimeFilter
)
from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    User,
    Subscription
)
from .admin_mixins import RelatedCountAdminMixin


admin.site.unregister(Group)
try:
    admin.site.unregister(AuthUser)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(RelatedCountAdminMixin, BaseUserAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        base_list_display = list(super().get_list_display(request=None))

        for field in ("first_name", "last_name", "is_staff"):
            if field in base_list_display:
                base_list_display.remove(field)

        self.list_display = (
            ["id"]
            + base_list_display
            + [
                "full_name",
                "avatar_preview",
                "recipes_count",
                "subscriptions_count",
                "followers_count",
            ]
        )

    list_filter = (
        "is_staff",
        "is_active",
        ("recipes", admin.EmptyFieldListFilter),
        ("subscriptions_for_author", admin.EmptyFieldListFilter),
        ("subscribers", admin.EmptyFieldListFilter),
    )
    search_fields = ("username", "email")
    ordering = ("id",)

    related_name = "recipes"
    count_field_name = "_recipes_count"
    display_name = "Рецептов"

    readonly_fields = ('avatar_preview_form',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Аватар пользователя", {
            "fields": ("avatar", "avatar_preview_form"),
        }),
    )

    def get_queryset(self, request):
        """Оптимизируем запрос — добавляем аннотации для подсчётов"""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _recipes_count=Count("recipes", distinct=True),
            _subscriptions_count=Count("subscribers", distinct=True),
            _followers_count=Count("subscriptions_for_author", distinct=True),
        )

    @admin.display(description="Превью аватара")
    @mark_safe
    def avatar_preview_form(self, obj):
        """Превью аватара на странице редактирования пользователя"""
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}" width="100" height="100" '
                'style="border-radius:50%;">'
            )
        return "—"

    @admin.display(description="Аватар")
    @mark_safe
    def avatar_preview(self, obj):
        """Превью аватара в списке пользователей"""
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}" width="50" height="50" '
                'style="border-radius: 50%;">'
            )
        return "—"

    @admin.display(description="ФИО")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    @admin.display(description="Рецептов")
    def recipes_count(self, obj):
        return obj._recipes_count

    @admin.display(description="Подписок")
    def subscriptions_count(self, obj):
        return obj._subscriptions_count

    @admin.display(description="Подписчиков")
    def followers_count(self, obj):
        return obj._followers_count


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = "__all__"

    def clean(self):
        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.image:
            self.fields["image"].help_text = mark_safe(
                f"""
                <div style="display:flex; gap:20px; align-items:center;">
                    <img src="{self.instance.image.url}"
                         style="max-width:120px; border-radius:6px;">
                </div>
                """
            )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscription_key', 'user', 'author')
    list_filter = ('user',)
    search_fields = (
        'user__email', 'user__username', 'author__email', 'author__username'
    )

    @admin.display(description='ID')
    def subscription_key(self, obj):
        return obj.id


@admin.register(Tag)
class TagAdmin(RelatedCountAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "slug", "recipes_count_display")
    search_fields = ("name", "slug")
    list_filter = (TagUsedInRecipesFilter,)

    related_name = "recipes"
    count_field_name = "_recipes_count"
    display_name = "Рецептов"


@admin.register(Ingredient)
class IngredientAdmin(RelatedCountAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipes_count_display")
    search_fields = ("name", "measurement_unit", "slug")
    list_filter = ("measurement_unit", UsedInRecipesFilter)

    related_name = "recipes"
    count_field_name = "_recipes_count"
    display_name = "Рецептов"


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    list_display = (
        "id",
        "name",
        "author_username",
        "cooking_time_display",
        "favorites_count",
        "show_ingredients",
        "show_tags",
        "show_image",
    )

    list_filter = (
        ("tags", RelatedOnlyFieldListFilter),
        ("author", RelatedOnlyFieldListFilter),
        CookingTimeFilter,
    )

    search_fields = (
        "name",
        "author__username",
        "author__email",
        "tags__name",
        "ingredients__name",
    )

    inlines = (RecipeIngredientInline,)

    @admin.display(description=mark_safe("Время<br>мин"))
    @mark_safe
    def cooking_time_display(self, recipe):
        return recipe.cooking_time

    @admin.display(description="Автор")
    def author_username(self, recipe):
        return recipe.author.username

    @admin.display(description="Продукты")
    @mark_safe
    def show_ingredients(self, recipe):
        return "<br>".join(
            f"{ri.ingredient.name} — {ri.amount} "
            f"{ri.ingredient.measurement_unit}"
            for ri in recipe.recipe_ingredients.all()
        )

    @admin.display(description="Теги")
    @mark_safe
    def show_tags(self, recipe):
        return "<br>".join(tag.name for tag in recipe.tags.all())

    @admin.display(description="Картинка")
    @mark_safe
    def show_image(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" width="60" '
                f'height="60" style="border-radius:6px;">'
            )
        return "—"

    @admin.display(description="В избранном")
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description="В избранном")
    def favorites_count_display(self, recipe):
        return recipe.favorites.count()

    @admin.display(description="В корзинах")
    def in_shopping_carts_count_display(self, recipe):
        return recipe.shoppingcarts.count()

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "name", "author", "image", "text", "cooking_time"
            ),
        }),
        ("Теги", {
            "fields": ("tags",),
        }),
        ("Статистика", {
            "fields": (
                "favorites_count_display",
                "in_shopping_carts_count_display",
            ),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = (
        "favorites_count_display",
        "in_shopping_carts_count_display",
    )


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(ShoppingCart)
@admin.register(Favorite)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "user_email")
    list_filter = ("user", "recipe")
    search_fields = ("user__email", "user__username", "recipe__name")

    @admin.display(description="Email пользователя")
    def user_email(self, obj):
        return obj.user.email
