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


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по времени готовки (динамические пороги на основе данных)"""
    title = "Время готовки"
    parameter_name = "cooking_time_group"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request).order_by("cooking_time")
        count = qs.count()

        if count == 0:
            return ()

        fast_limit = qs[count // 3].cooking_time
        medium_limit = qs[2 * count // 3].cooking_time

        return (
            ("fast", f"быстрее {fast_limit} мин ({qs.filter(cooking_time__lt=fast_limit).count()})"),
            ("medium", f"до {medium_limit} мин ({qs.filter(cooking_time__gte=fast_limit, cooking_time__lt=medium_limit).count()})"),
            ("long", f"долго ({qs.filter(cooking_time__gte=medium_limit).count()})"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        qs = queryset.order_by("cooking_time")
        count = qs.count()

        if not count or value not in ("fast", "medium", "long"):
            return queryset

        fast_limit = qs[count // 3].cooking_time
        medium_limit = qs[2 * count // 3].cooking_time

        if value == "fast":
            return queryset.filter(cooking_time__lt=fast_limit)
        elif value == "medium":
            return queryset.filter(cooking_time__gte=fast_limit, cooking_time__lt=medium_limit)
        return queryset.filter(cooking_time__gte=medium_limit)
