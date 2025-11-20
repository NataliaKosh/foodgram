from django.contrib import admin
from django.db.models import Count


class BaseUsedInRecipesFilter(admin.SimpleListFilter):
    """Базовый фильтр — используется ли объект в рецептах"""

    LOOKUPS = (
        ("yes", "Используются"),
        ("no", "Не используются"),
    )

    RELATED_NAME = None
    COUNT_FIELD = "used_count"

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        queryset = queryset.annotate(
            **{self.COUNT_FIELD: Count(self.RELATED_NAME)}
        )

        value = self.value()
        if value == "yes":
            return queryset.filter(**{f"{self.COUNT_FIELD}__gt": 0})
        elif value == "no":
            return queryset.filter(**{f"{self.COUNT_FIELD}": 0})
        return queryset


class UsedInRecipesFilter(BaseUsedInRecipesFilter):
    """Фильтр для ингредиентов — используются ли в рецептах"""
    title = "Есть в рецептах"
    parameter_name = "used_in_recipes"

    RELATED_NAME = "recipes"
    COUNT_FIELD = "recipes_count"


class TagUsedInRecipesFilter(BaseUsedInRecipesFilter):
    """Фильтр для тегов — используются ли в рецептах"""
    title = "Есть в рецептах"
    parameter_name = "used_in_recipes"

    RELATED_NAME = "recipes"
    COUNT_FIELD = "recipe_count"


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по времени готовки"""

    title = "Время готовки"
    parameter_name = "cooking_time_group"

    def lookups(self, request, model_admin):
        cooking_times = (
            model_admin.get_queryset(request)
            .order_by("cooking_time")
            .values_list("cooking_time", flat=True)
            .distinct()
        )

        if cooking_times.count() < 3:
            return ()

        fast_limit = cooking_times[cooking_times.count() // 3]
        medium_limit = cooking_times[2 * cooking_times.count() // 3]

        self.time_ranges = {
            "fast": (0, fast_limit),
            "medium": (fast_limit, medium_limit),
            "long": (medium_limit, 10**6),
        }

        return (
            ("fast", f"быстрее {fast_limit} мин"),
            ("medium", f"до {medium_limit} мин"),
            ("long", "долго"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value not in self.time_ranges:
            return queryset

        return queryset.filter(cooking_time__range=self.time_ranges[value])


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтр пользователей по наличию рецептов"""
    title = "Есть рецепты"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть рецепты"),
            ("no", "Нет рецептов"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    """Фильтр пользователей по наличию подписок"""
    title = "Есть подписки"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписки"),
            ("no", "Нет подписок"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscribers__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscribers__isnull=True)
        return queryset


class HasFollowersFilter(admin.SimpleListFilter):
    """Фильтр пользователей по наличию подписчиков"""
    title = "Есть подписчики"
    parameter_name = "has_followers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Есть подписчики"),
            ("no", "Нет подписчиков"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscriptions_for_author__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscriptions_for_author__isnull=True)
        return queryset