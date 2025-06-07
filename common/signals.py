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

from .models import ImportProcess
from .utils.websocket_utils import send_alert,fetch_import_processes,send_import_process_percent
from core.middleware import get_current_user

@receiver(pre_save, sender=ImportProcess)
def import_process_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    if sender.objects.filter(id=instance.id).exists():
        old_instance = sender.objects.filter(id=instance.id).first()

        if old_instance.status != instance.status:
            if instance.status == "in_progress":
                fetch_import_processes(
                    message={"status":instance.status,"model":instance.model_name,"activeCompany": {"id":instance.company.id}},
                    room=f"private_{instance.user.uuid}"
                )
            elif instance.status == "completed":
                fetch_import_processes(
                    message={"status":instance.status,"model":instance.model_name,"activeCompany": {"id":instance.company.id}},
                    room=f"private_{instance.user.uuid}"
                )
                send_alert(
                    message={"message":f"{instance.model_name} items imported successfully!","status":"success"},
                    room=f"private_{instance.user.uuid}"
                )
            elif instance.status == "rejected":
                fetch_import_processes(
                    message={"status":instance.status,"model":instance.model_name,"activeCompany": {"id":instance.company.id}},
                    room=f"private_{instance.user.uuid}"
                )
                send_alert(
                    message={"message":f"{instance.model_name} items import rejected due to invalid data!","status":"error"},
                    room=f"private_{instance.user.uuid}"
                )
        if old_instance.progress != instance.progress:
            send_import_process_percent(
                message={"progress":instance.progress,"task":instance.task_id},
                room=f"private_{instance.user.uuid}"
            )

@receiver(post_delete, sender=ImportProcess)
def import_process_delete(sender, instance, **kwargs):
    fetch_import_processes(
        message={"status":instance.status,"model":instance.model_name,"activeCompany": {"id":instance.company.id}},
        room=f"private_{instance.user.uuid}"
    )