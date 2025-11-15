from django.contrib import admin
from django.db.models import Count


class RelatedCountAdminMixin:
    """Миксин для подсчёта количества связанных объектов"""
    related_name = None
    count_field_name = None
    display_name = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        field_name = self.count_field_name or self.related_name
        if field_name and self.related_name:
            qs = qs.annotate(
                **{field_name: Count(self.related_name, distinct=True)}
            )
        return qs

    def count_display(self, obj):
        field_name = self.count_field_name or self.related_name
        return getattr(obj, field_name, 0)

    @property
    def recipes_count_display(self):
        """Создает метод для отображения количества рецептов"""
        def method(obj):
            return self.count_display(obj)
        method.__name__ = 'recipes_count_display'
        method.short_description = self.display_name
        return admin.display(description=self.display_name)(method)
