import django_filters
from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(method='filter_shopping_cart')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        qs = queryset.filter(favorites__user=user) if value else queryset.exclude(favorites__user=user)
        return qs.distinct()  # важный distinct

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        qs = queryset.filter(shopping_cart__user=user) if value else queryset.exclude(shopping_cart__user=user)
        return qs.distinct()
