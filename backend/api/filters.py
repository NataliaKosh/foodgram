import django_filters
from recipes.models import Recipe, Ingredient


class RecipeFilter(django_filters.FilterSet):
    """Фильтр рецептов по тегам, избранному, корзине и автору"""

    is_favorited = django_filters.NumberFilter(method='filter_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_shopping_cart'
    )
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = django_filters.NumberFilter(field_name='author__id')

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset

        qs = (
            queryset.filter(favorite_recipe__user=user)
            if value
            else queryset.exclude(favorite_recipe__user=user)
        )
        return qs.distinct()

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset

        qs = (
            queryset.filter(shoppingcart_recipe__user=user)
            if value
            else queryset.exclude(shoppingcart_recipe__user=user)
        )
        return qs.distinct()

    class Meta:
        model = Recipe
        fields = [
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        ]


class IngredientFilter(django_filters.FilterSet):
    """Фильтр ингредиентов по названию"""
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = ['name']
