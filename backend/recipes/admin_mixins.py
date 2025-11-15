from django.contrib import admin
from django.db.models import Count


class RelatedCountAdminMixin:
    """Миксин для подсчёта количества связанных объектов"""
    related_name = None
    count_field_name = None
    display_name = None

    count_list_display = []

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.related_name and self.count_field_name:
            qs = qs.annotate(**{
                self.count_field_name: Count(
                    self.related_name, distinct=True
                )
            })
        return qs

    def count_display(self, obj):
        """Возвращает значение аннотированного поля"""
        return getattr(obj, self.count_field_name, 0)

    @classmethod
    def register_count_display(cls):
        """Создаёт метод для list_display"""
        if cls.count_field_name and cls.display_name:
            method_name = cls.count_field_name.strip("_") + "_count"
            setattr(
                cls,
                method_name,
                admin.display(description=cls.display_name)(
                    cls.count_display
                )
            )
            cls.count_list_display.append(method_name)
