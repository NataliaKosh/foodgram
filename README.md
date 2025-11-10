# Foodgram - Платформа для публикации рецептов

## О проекте

Foodgram — это современная веб-платформа, где пользователи могут публиковать свои кулинарные рецепты, добавлять понравившиеся рецепты в избранное, подписываться на публикации других авторов и пользоваться удобным сервисом «Список покупок».

## Автор

* Наталия Васильева
* E-mail: nataliakosh17@gmail.com


## Основные возможности

Для всех пользователей:

* Просмотр рецептов — доступ к библиотеке рецептов от сообщества
* Просмотр профилей — знакомство с авторами и их рецептами
* Поиск и фильтрация — поиск рецептов по ингредиентам и фильтрация по тегам

Для зарегистрированных пользователей:

* Публикация рецептов — создание и редактирование собственных рецептов
* Избранное — сохранение понравившихся рецептов
* Подписки — слежение за публикациями любимых авторов
* Список покупок — формирование списка продуктов для выбранных рецептов
* Личный кабинет — управление профилем и настройками аккаунта

## Технологии

Backend:

* Python + Django
* Django REST Framework
* Djoser для аутентификации
* Simple JWT
* Token-based авторизация
* Pillow для работы с изображениями

Frontend: React (SPA)

База данных: PostgreSQL (psycopg2-binary 2.9.9)

Деплой: Docker + Nginx

## Команды для запуска и развертывания

Локальный запуск без Docker:

1. Создать и активировать виртуальное окружение:

   * python -m venv venv
   * source venv/bin/activate   (Linux/macOS)
   * venv\Scripts\activate      (Windows)
2. Установить зависимости:

   * pip install --upgrade pip
   * pip install -r requirements.txt
3. Создать .env файл с переменными окружения:
   SECRET_KEY=ваш_секретный_ключ
   DEBUG=True
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=ваш_пароль
   POSTGRES_DB=foodgram
   DB_HOST=localhost
   DB_PORT=5432
   ALLOWED_HOSTS=localhost,127.0.0.1
4. Применить миграции:

   * python manage.py makemigrations
   * python manage.py migrate
5. Импорт данных (фикстуры):

   * python manage.py import_tags
   * python manage.py import_ingredients
6. Создать суперпользователя (для доступа к админке):

   * python manage.py createsuperuser
7. Запустить сервер разработки:

   * python manage.py runserver

Доступы после запуска:

* API документация: http://127.0.0.1:8000/api/
* Админка Django: http://127.0.0.1:8000/admin/
* Сервер: http://127.0.0.1:8000/

Запуск через Docker (продакшн):

1. Создать .env с нужными переменными (аналогично локальному запуску)
2. Запустить Docker Compose:

   * docker compose -f docker_compose.production.yml up -d
3. Выполнить миграции и собрать статику:

   * docker compose run --rm backend python manage.py makemigrations
   * docker compose run --rm backend python manage.py migrate
   * docker compose exec backend python manage.py collectstatic --noinput
4. Импорт данных:

   * docker compose run --rm backend python manage.py import_tags
   * docker compose run --rm backend python manage.py import_ingredients

Команды для тестов:

* Проверка кода линтером: flake8 backend/

Полезные ссылки:

* Документация Django REST Framework: https://www.django-rest-framework.org/
* Djoser — аутентификация Django REST: https://djoser.readthedocs.io/
* Docker документация: https://docs.docker.com/
---