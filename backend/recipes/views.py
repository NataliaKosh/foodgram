from django.shortcuts import redirect
from django.http import Http404

from .models import Recipe


def short_link_redirect(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404("Рецепт не найден")
    return redirect(f'/recipes/{pk}/')
