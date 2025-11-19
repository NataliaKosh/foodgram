import short_url

from django.shortcuts import redirect

from .models import Recipe


def short_link_redirect(request, short_code: str):
    try:
        recipe_id = short_url.decode_url(short_code)

        if not Recipe.objects.filter(pk=recipe_id).exists():
            return redirect('/not_found/')

        return redirect(f'/recipes/{recipe_id}/')

    except (ValueError, KeyError):
        return redirect('/not_found/')
