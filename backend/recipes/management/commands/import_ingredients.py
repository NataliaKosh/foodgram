from recipes.models import Ingredient
from .base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = "Импорт ингредиентов из data/ingredients.json"
    model = Ingredient
    filepath = 'ingredients.json'
