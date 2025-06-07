from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.core.signals import request_finished

from .models import Notification
from common.utils.websocket_utils import send_notification
from core.middleware import get_current_user

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if created:
        send_notification(message=instance.message,room=f"private_{instance.user.uuid}")
        

@receiver(post_delete, sender=Notification)
def notification_deleted(sender, instance, **kwargs):
    send_notification(message="deleted",room=f"private_{instance.user.uuid}")