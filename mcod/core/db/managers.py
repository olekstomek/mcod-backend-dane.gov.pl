from django.db import models


class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_removed=True)
