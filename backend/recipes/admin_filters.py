from django.contrib import admin
from django.db.models import Count


class UsedInRecipesFilter(admin.SimpleListFilter):
    """Фильтр для ингредиентов — используются ли в рецептах"""
    title = "Есть в рецептах"
    parameter_name = "used_in_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Используются"),
            ("no", "Не используются"),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(recipes_count=Count("recipes"))
        if self.value() == "yes":
            return queryset.filter(recipes_count__gt=0)
        if self.value() == "no":
            return queryset.filter(recipes_count=0)
        return queryset


class TagUsedInRecipesFilter(admin.SimpleListFilter):
    """Фильтр для тегов — используются ли в рецептах"""
    title = "Есть в рецептах"
    parameter_name = "used_in_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Используются"),
            ("no", "Не используются"),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(recipe_count=Count("recipes"))
        if self.value() == "yes":
            return queryset.filter(recipe_count__gt=0)
        if self.value() == "no":
            return queryset.filter(recipe_count=0)
        return queryset
