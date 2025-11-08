from django.shortcuts import get_object_or_404

from djoser.serializers import SetPasswordSerializer
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from djoser.serializers import UserCreateSerializer

from api.pagination import StandardPagination
from .models import Subscription, User
from .serializers import (
    SetAvatarSerializer,
    SubscriptionListSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с пользователями.
    """
    queryset = User.objects.all()
    pagination_class = StandardPagination
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """
        Вызов сериализатора создания пользователя или подписок
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'subscriptions':
            return SubscriptionListSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Настройки разрешений в соответствии с спецификацией
        """
        if self.action in ['create', 'list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Получение данных текущего пользователя
        """
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'patch', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        """
        Управление аватаром
        """
        user = request.user
        if request.method in ['PUT', 'PATCH']:
            serializer = SetAvatarSerializer(
                user, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            avatar_url = None
            if user.avatar:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({
                'avatar': avatar_url
            }, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка и отписка на пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if author == user:
                return Response(
                    {'detail': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(
                user=user, author=author
            ).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=user, author=author
            )
            serializer = SubscriptionListSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription_exists = Subscription.objects.filter(
                user=user,
                author=author
            ).exists()

            if not subscription_exists:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        serializer = SubscriptionListSerializer(
            page if page is not None else authors,
            many=True,
            context={'request': request}
        )
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password_legacy(self, request):
        """Старый endpoint для фронта, использует Джосер"""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
