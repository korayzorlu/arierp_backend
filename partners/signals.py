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

from .models import Partner
from common.utils.websocket_utils import send_alert,fetch_import_processes,send_import_process_percent
from core.middleware import get_current_user

@receiver(pre_save, sender=Partner)
def import_process_update(sender, instance, **kwargs):
    if sender.objects.filter(id=instance.id).exists():
        old_instance = sender.objects.filter(id=instance.id).first()

        # send_alert(
        #     message={"message":f"Partner signals test alert successfully!","status":"success"},
        #     room=f"private_{get_current_user().id}"
        # )

