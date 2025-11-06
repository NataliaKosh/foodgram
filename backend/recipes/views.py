from django.shortcuts import redirect, get_object_or_404
from .models import Recipe


def short_link_redirect(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{pk}/')
