from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.signals import request_finished
from django.core.files.base import ContentFile
from django.core.files import File

from PIL import Image
import io
import os

from .models import Invitation

from notifications.models import Notification

@receiver(post_save, sender=Invitation)
def invitation_created(sender, instance, created, **kwargs):
    if created:

        notification = Notification.objects.create(
            user = instance.recipient,
            message = f"{instance.sender.first_name} {instance.sender.last_name} has invited you to join {instance.company.name}.",
            navigation = "/invitations"
        )

        if instance.sender.profile and instance.sender.profile.image and instance.sender.profile.image.name:
            notification.image = instance.sender.profile.image
        else:
            static_image_path = os.path.join(settings.BASE_DIR, "static/images/global/user-2.png")
            with open(static_image_path, "rb") as f:
                notification.image.save("user.jpg", File(f), save=True)

        notification.save()