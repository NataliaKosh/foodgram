from django.template.loader import render_to_string
from django.utils.timezone import now


def generate_shopping_list_text(ingredients, recipes):
    """Формирует текст для файла списка покупок"""

    date_str = now().strftime('%d.%m.%Y')

    return render_to_string(
        'shopping_list.txt',
        {
            'ingredients': ingredients,
            'recipes': recipes,
            'date': date_str,
        }
    )
