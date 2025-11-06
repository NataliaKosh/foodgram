from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    RecipeMinifiedSerializer,
)
from .pagination import StandardPagination
from .permissions import IsAuthorOrReadOnly
# from .filters import RecipeFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""
    queryset = Recipe.objects.all()
    # serializer_class = RecipeSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthorOrReadOnly]
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_class = RecipeFilter
    # ordering_fields = ['created']
    # ordering = ['-created']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление и удаление рецепта в избранное"""
        return self._add_remove_relation(request, pk, Favorite)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок"""
        return self._add_remove_relation(request, pk, ShoppingCart)

    def _add_remove_relation(self, request, pk, model):
        """Метод для добавления и удаления связей"""
        user = request.user
        action_name = 'избранное' if model is Favorite else 'список покупок'

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {
                        'errors': (
                            f'Рецепт "{recipe.name}" уже добавлен '
                            f'в {action_name}'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=user, recipe_id=pk).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': 'Рецепт не был добавлен'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок, только для авторизованных"""
        user = request.user

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        text_content = "Foodgram  Список покупок\n"
        text_content += "=" * 30 + "\n\n"

        for ingredient in ingredients:
            text_content += (
                f"• {ingredient['ingredient__name']} - "
                f"{ingredient['total_amount']} "
                f"{ingredient['ingredient__measurement_unit']}\n"
            )

        text_content += f"\nВсего ингредиентов: {len(ingredients)}"
        text_content += "\n\nПриятного аппетита!"

        response = HttpResponse(
            text_content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт"""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            f'/api/recipes/{recipe.id}/'
        )
        return Response({'short-link': short_link})


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для избранных рецептов"""
    serializer_class = RecipeMinifiedSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Recipe.objects.filter(
            favorites__user=user
        ).order_by('-favorites__id')

    def list(self, request, *args, **kwargs):
        """Список избранных рецептов с фильтрацией по тегам"""
        queryset = self.get_queryset()

        # Фильтрация по тегам
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
