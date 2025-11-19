from django.contrib import admin
from django.db.models import Count


class RelatedCountAdminMixin:
    """Миксин для подсчёта связанных объектов"""

    related_name = None
    count_field_name = None
    display_name = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if self.related_name and self.count_field_name:
            qs = qs.annotate(
                **{self.count_field_name: Count(
                    self.related_name, distinct=True
                )}
            )

        return qs

    def get_list_display(self, request):
        """Добавляет в list_display метод для отображения количества"""
        list_display = list(super().get_list_display(request))

        if self.count_field_name and self.display_name:
            method_name = f"{self.related_name}_count_display"

            # Создаём метод если его ещё нет
            if not hasattr(self, method_name):

                @admin.display(description=self.display_name)
                def count_method(obj, field=self.count_field_name):
                    return getattr(obj, field, 0)

                setattr(self, method_name, count_method)

            list_display.append(method_name)

        return list_display
