from django.core.signals import request_finished
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from datetime import timedelta

from .models import *

@receiver(post_save, sender=Subscription)
def subscription_post(sender, instance, created, **kwargs):
    with transaction.atomic():
        if created:
            instance.endDate = instance.startDate + timedelta(days = instance.duration)
            instance.save()

