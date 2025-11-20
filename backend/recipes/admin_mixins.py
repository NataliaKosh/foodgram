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
