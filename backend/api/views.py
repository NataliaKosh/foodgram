from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.utils.timezone import now
from django.template.loader import render_to_string
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
    Subscription,
    User
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    RecipeMinifiedSerializer,
    SetAvatarSerializer,
    UserWithRecipesSerializer,
    UserSerializer,
)
from .pagination import StandardPagination
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter


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
    serializer_class = RecipeSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
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
        """Добавление или удаление рецепта из избранного / корзины."""
        action_name = model._meta.verbose_name
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method != 'POST':
            get_object_or_404(
                model,
                user=request.user,
                recipe_id=pk
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        _, created = model.objects.get_or_create(
            user=request.user,
            recipe_id=pk,
        )
        if not created:
            raise ValidationError(
                f'Рецепт "{recipe.name}" уже добавлен в {action_name}'
            )

        return Response(
            RecipeMinifiedSerializer(
                get_object_or_404(Recipe, pk=pk),
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
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
            recipe__in_shopping_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        recipes = Recipe.objects.filter(
            in_shopping_carts__user=user
        ).select_related('author')

        content = render_to_string(
            'shopping_list.txt',
            {
                'ingredients': ingredients,
                'recipes': recipes,
                'date': now().strftime('%d.%m.%Y'),
            }
        )

        return FileResponse(
            content,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain',
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(
                {'detail': f'Рецепт с id={pk} не найден'}
            )

        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse('recipe-short-link', args=[pk])
                )
            }
        )


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для работы с пользователями.
    """
    queryset = User.objects.all()
    pagination_class = StandardPagination
    permission_classes = [permissions.AllowAny]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Получение данных текущего пользователя
        """
        return Response(
            UserSerializer(request.user, context={'request': request}).data
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        """Управление аватаром"""
        user = request.user

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=204)

        serializer = SetAvatarSerializer(
            user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'avatar': request.build_absolute_uri(user.avatar.url)
                if user.avatar else None
            },
            status=200
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Подписка и отписка на пользователя."""
        user = request.user

        if request.method != 'POST':
            get_object_or_404(Subscription, user=user, author_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if id == user.pk:
            raise ValidationError({'detail': 'Нельзя подписаться на себя'})

        author = get_object_or_404(User, pk=id)

        _, created = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if not created:
            raise ValidationError(
                {
                    'detail': (
                        f'Вы уже подписаны на пользователя '
                        f'{author.username}'
                    )
                }
            )

        return Response(
            UserWithRecipesSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Подписки с пагинацией"""
        user = request.user
        author_ids = user.subscribers.values_list('author', flat=True)
        queryset = User.objects.filter(id__in=author_ids)
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                page, many=True, context={'request': request}
            ).data
        )
