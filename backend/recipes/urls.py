from django.urls import path

from .views import short_link_redirect

app_name = 'recipes'


urlpatterns = [
    path('s/<str:pk>/', short_link_redirect, name='short-link'),
]
