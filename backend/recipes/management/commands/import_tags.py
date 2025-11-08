from django.core.management.base import BaseCommand
from recipes.models import Tag
import json
import os


class Command(BaseCommand):
    help = "Импорт тегов из data/tags.json"

    def handle(self, *args, **kwargs):
        filepath = os.path.join('data', 'tags.json')
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            Tag.objects.get_or_create(
                name=item['name'],
                slug=item['slug']
            )
        self.stdout.write(self.style.SUCCESS("Теги импортированы"))
