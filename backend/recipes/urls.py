from django.urls import path

from .views import short_link_redirect


urlpatterns = [
    path('s/<int:pk>/', short_link_redirect, name='recipe-short-link'),
]
