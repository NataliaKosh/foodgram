from recipes.models import Tag
from .base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Импорт тегов из data/tags.json"
    model = Tag
    filepath = 'tags.json'
