from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


USERNAME_VALIDATOR = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Username может содержать только буквы, цифры и @/./+/-/_'
)


class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField(
        max_length=254,
        verbose_name='Адрес электронной почты',
        unique=True
    )
    username = models.CharField(
        max_length=150,
        verbose_name='Юзернейм',
        unique=True,
        validators=[USERNAME_VALIDATOR]
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/',
        blank=True,
        null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('email',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Модель подписок на пользователей"""
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='subscribers',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='followers',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(
        verbose_name='Дата подписки',
        # auto_now_add=True,
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        ordering = ['-created']

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
