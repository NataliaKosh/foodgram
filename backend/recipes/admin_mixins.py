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
            qs = qs.annotate(
                **{self.count_field_name: Count(
                    self.related_name, distinct=True
                )}
            )
        return qs

    def count_display(self, obj):
        field_name = self.count_field_name
        return getattr(obj, field_name, 0)

    def get_count_display(self):
        """Возвращает метод для отображения в list_display с description"""
        return admin.display(description=self.display_name)(
            self.count_display
        )

    def __init_subclass__(cls, **kwargs):
        """Автоматически добавляем count_display в count_list_display"""
        super().__init_subclass__(**kwargs)
        if cls.count_field_name and cls.display_name:
            method_name = f"{cls.count_field_name}_display"
            setattr(cls, method_name, cls.get_count_display(cls))
            cls.count_list_display.append(method_name)
