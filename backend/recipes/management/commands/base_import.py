import json
import os

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта JSON в модель Django."""

    model = None
    filepath = None

    def handle(self, *args, **kwargs):
        if not self.model or not self.filepath:
            self.stderr.write(
                self.style.ERROR("Не указаны model или filepath")
            )
        return

        try:
            full_path = os.path.join('data', self.filepath)
            with open(full_path, encoding='utf-8') as f:
                created_objs = self.model.objects.bulk_create(
                    self.model(**item) for item in json.load(f)
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(created_objs)} объектов {self.model.__name__} "
                    f"из файла {self.filepath} импортировано"
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Ошибка импорта из файла {self.filepath}: {e}"
                )
            )
