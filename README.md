# Foodgram - Платформа для публикации рецептов

## О проекте
Foodgram — это современная веб-платформа, где пользователи могут публиковать свои кулинарные рецепты, добавлять понравившиеся рецепты в избранное, подписываться на публикации других авторов и пользоваться удобным сервисом «Список покупок».

## Основные возможности

### Для всех пользователей
- ** Просмотр рецептов** - Доступ к библиотеке рецептов от сообщества
- ** Просмотр профилей** - Знакомство с авторами и их рецептами
- ** Поиск и фильтрация** - Поиск рецептов по ингредиентам и фильтрация по тегам

### Для зарегистрированных пользователей
- ** Публикация рецептов** - Создание и редактирование собственных рецептов
- ** Избранное** - Сохранение понравившихся рецептов
- ** Подписки** - Слежение за публикациями любимых авторов
- ** Список покупок** - Формирование списка продуктов для выбранных рецептов
- ** Личный кабинет** - Управление профилем и настройками аккаунта

### Технологии

**Backend:**
- Python + Django 5.2.7
- Django REST Framework 3.16.1
- Djoser 2.3.3 для аутентификации
- Simple JWT 5.5.1
- Token-based авторизация
- Pillow 12.0.0 для работы с изображениями

**Frontend:** React (SPA)

**База данных:** PostgreSQL (psycopg2-binary 2.9.11)

**Деплой:** Docker + Nginx

## Примеры запросов API

### 1. Аутентификация

**Получение токена:**
```
POST http://foodgram.example.org/api/auth/token/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Удаление токена:**
```
POST http://foodgram.example.org/api/auth/token/logout/
Authorization: Token your_token_here
```

### 2. Пользователи

**Регистрация пользователя:**
```
POST http://foodgram.example.org/api/users/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "username": "newuser",
  "first_name": "Иван",
  "last_name": "Петров",
  "password": "securepassword123"
}
```

**Получить текущего пользователя:**
```
GET http://foodgram.example.org/api/users/me/
Authorization: Token your_token_here
```

**Изменить пароль:**
```
POST http://foodgram.example.org/api/users/set_password/
Authorization: Token your_token_here
Content-Type: application/json

{
  "new_password": "newsecurepassword123",
  "current_password": "oldpassword"
}
```

### 3. Рецепты

**Получить список рецептов с фильтрацией:**
```
GET http://foodgram.example.org/api/recipes/?page=1&limit=10&is_favorited=1&tags=breakfast&author=5
```

**Создать рецепт:**
```
POST http://foodgram.example.org/api/recipes/
Authorization: Token your_token_here
Content-Type: application/json

{
  "ingredients": [
    {"id": 1, "amount": 200},
    {"id": 2, "amount": 2}
  ],
  "tags": [1, 2],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "Новый рецепт",
  "text": "Описание нового рецепта",
  "cooking_time": 30
}
```

**Обновить рецепт:**
```
PATCH http://foodgram.example.org/api/recipes/123/
Authorization: Token your_token_here
Content-Type: application/json

{
  "name": "Обновленное название рецепта",
  "text": "Обновленное описание",
  "cooking_time": 35,
  "ingredients": [
    {"id": 1, "amount": 250},
    {"id": 3, "amount": 1}
  ],
  "tags": [1, 3]
}
```

### 4. Избранное и корзина

**Добавить в избранное:**
```
POST http://foodgram.example.org/api/recipes/123/favorite/
Authorization: Token your_token_here
```

**Удалить из избранного:**
```
DELETE http://foodgram.example.org/api/recipes/123/favorite/
Authorization: Token your_token_here
```

**Добавить в список покупок:**
```
POST http://foodgram.example.org/api/recipes/123/shopping_cart/
Authorization: Token your_token_here
```

**Скачать список покупок:**
```
GET http://foodgram.example.org/api/recipes/download_shopping_cart/
Authorization: Token your_token_here
```

### 5. Подписки

**Подписаться на пользователя:**
```
POST http://foodgram.example.org/api/users/5/subscribe/
Authorization: Token your_token_here
```

**Получить мои подписки:**
```
GET http://foodgram.example.org/api/users/subscriptions/?page=1&limit=10&recipes_limit=3
Authorization: Token your_token_here
```

### 6. Ингредиенты и теги

**Поиск ингредиентов:**
```
GET http://foodgram.example.org/api/ingredients/?name=карто
```

**Получить все теги:**
```
GET http://foodgram.example.org/api/tags/
```