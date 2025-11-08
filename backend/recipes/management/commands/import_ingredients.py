from django.core.management.base import BaseCommand
from recipes.models import Ingredient
import json
import os


class Command(BaseCommand):
    help = "Импорт ингредиентов из data/ingredients.json"

    def handle(self, *args, **kwargs):
        filepath = os.path.join('data', 'ingredients.json')
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
        self.stdout.write(self.style.SUCCESS("Ингредиенты импортированы"))
