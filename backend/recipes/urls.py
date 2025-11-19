from django.urls import path

from .views import short_link_redirect

app_name = 'recipes'

urlpatterns = [
    path('s/<str:short_code>/', short_link_redirect, name='recipe-short-link'),
]
