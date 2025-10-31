from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, permissions
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
    RecipeListSerializer,
    RecipeCreateSerializer,
    RecipeUpdateSerializer,
    RecipeMinifiedSerializer,
)
from .pagination import StandardPagination
from .permissions import IsAuthorOrReadOnly


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

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""
    queryset = Recipe.objects.all()
    pagination_class = StandardPagination

    def get_permissions(self):
        """
        Настройки разрешений в соответствии с спецификацией
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [
                permissions.IsAuthenticated, IsAuthorOrReadOnly
            ]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create']:
            return RecipeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RecipeUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user

        # Фильтрация по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(favorites__user=user)
            elif is_favorited == '0':
                queryset = queryset.exclude(favorites__user=user)

        # Фильтрация по корзине
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart and user.is_authenticated:
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(shopping_cart__user=user)
            elif is_in_shopping_cart == '0':
                queryset = queryset.exclude(shopping_cart__user=user)

        # Фильтрация по автору
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Фильтрация по тегам
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Сортировка по дате
        queryset = queryset.order_by('-created')

        return queryset.select_related('author').prefetch_related(
            'tags', 'recipe_ingredients__ingredient'
        )

    def _save_with_author(self, serializer):
        serializer.save(author=self.request.user)
    perform_create = _save_with_author
    perform_update = _save_with_author

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
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                obj = model.objects.get(user=user, recipe=recipe)
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
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
