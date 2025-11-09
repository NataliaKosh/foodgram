from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, status, permissions, filters, serializers
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
from .services.shopping_list import generate_shopping_list_text
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

        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=request.user,
                recipe_id=pk,
            )
            if not created:
                raise ValidationError(
                    f'Рецепт уже добавлен в {action_name}'
                )
            return Response(
                RecipeMinifiedSerializer(
                    get_object_or_404(
                        Recipe,
                        pk=pk
                    ),
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            raise ValidationError(
                f'Рецепт не был добавлен в {action_name}'
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок, только для авторизованных"""
        user = request.user

        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart_set__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        recipes = Recipe.objects.filter(
            shoppingcart_set__user=user
        ).select_related('author')

        content = generate_shopping_list_text(
            ingredients=ingredients,
            recipes=recipes,
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
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('recipe-short-link', kwargs={'pk': recipe.pk})
            )}
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

        _, created = Subscription.objects.get_or_create(user=user, author_id=id)
        if not created:
            raise ValidationError({'detail': 'Вы уже подписаны на пользователя'})

        return Response(
            UserWithRecipesSerializer(
                get_object_or_404(User, pk=id),
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
        subscriptions = Subscription.objects.filter(user=user)
        authors = [sub.author for sub in subscriptions]
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(authors, request)
        serializer = UserWithRecipesSerializer(
            page if page is not None else authors,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password_legacy(self, request):
        """Старый endpoint для фронта, вручную меняет пароль."""
        class PasswordChangeSerializer(serializers.Serializer):
            current_password = serializers.CharField(required=True)
            new_password = serializers.CharField(
                required=True,
                validators=[validate_password]
            )

            def validate_current_password(self, value):
                if not request.user.check_password(value):
                    raise serializers.ValidationError(
                        "Текущий пароль неверен"
                    )
                return value

        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(
            serializer.validated_data['new_password']
        )
        request.user.save()
        return Response(status=204)
