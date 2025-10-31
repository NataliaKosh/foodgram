import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки base64 изображений"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            decoded_file = base64.b64decode(imgstr)
            file_extension = imghdr.what(None, decoded_file)
            if not file_extension:
                raise serializers.ValidationError(
                    'Некорректный формат изображения'
                )
            file_name = f"{uuid.uuid4()}.{file_extension}"
            data = ContentFile(decoded_file, name=file_name)
        return super().to_internal_value(data)
