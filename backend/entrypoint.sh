#!/bin/sh

echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

echo "📦 Собираем статику..."
python manage.py collectstatic --noinput

echo "🥕 Загружаем ингредиенты..."
python manage.py shell <<EOF
from recipes.models import Ingredient
import json, os
if not Ingredient.objects.exists():
    path = "/app/data/ingredients.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            Ingredient.objects.get_or_create(
                name=item["name"],
                measurement_unit=item["measurement_unit"]
            )
        print(f"✅ Загружено {len(data)} ингредиентов")
    else:
        print("⚠️ Файл ингредиентов не найден")
else:
    print("✅ Ингредиенты уже есть в БД, пропускаем")
EOF

echo "🚀 Запуск Gunicorn..."
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8080 --workers 3
