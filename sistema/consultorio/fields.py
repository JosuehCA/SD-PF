from django.db import models

from .encryption import encrypt, decrypt


class EncryptedTextField(models.TextField):
    """TextField that stores data encrypted at rest using AES-256-GCM."""

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return decrypt(value)
        except Exception:
            return value

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return encrypt(value)


class EncryptedCharField(models.CharField):
    """CharField that stores data encrypted at rest using AES-256-GCM."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 512)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return decrypt(value)
        except Exception:
            return value

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return encrypt(value)
