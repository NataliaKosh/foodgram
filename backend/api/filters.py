import django_filters
from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов по автору, тегам, избранному и списку покупок"""
    is_favorited = django_filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        elif value is False and user.is_authenticated:
            return queryset.exclude(favorites__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        elif value is False and user.is_authenticated:
            return queryset.exclude(shopping_cart__user=user)
        return queryset
