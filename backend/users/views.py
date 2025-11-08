from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password

from rest_framework import permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from djoser.views import UserViewSet as DjoserUserViewSet

from api.pagination import StandardPagination
from .models import Subscription, User
from .serializers import (
    SetAvatarSerializer,
    SubscriptionListSerializer,
    UserSerializer,
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
        methods=['put', 'patch'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        """
        Обновление аватара текущего пользователя
        """
        user = request.user
        serializer = SetAvatarSerializer(
            user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        avatar_url = (
            request.build_absolute_uri(user.avatar.url)
            if user.avatar else None
        )
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe'
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
