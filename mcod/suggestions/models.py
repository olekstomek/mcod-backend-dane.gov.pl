from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
from mcod.suggestions.tasks import send_data_suggestion


class Suggestion(models.Model):
    notes = models.TextField()
    send_date = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=Suggestion)
def handle_suggestion_post_save(sender, instance, *args, **kwargs):
    data_suggestion = {"notes": instance.notes}
    send_data_suggestion.s(instance.id, data_suggestion).apply_async()
