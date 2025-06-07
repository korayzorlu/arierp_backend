from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def fetch_import_processes(message,room):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room,
        {
            "type": "fetch_import_processes",
            "message": message,
        }
    )

def send_alert(message,room):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room,
        {
            "type": "send_alert",
            "message": message,
        }
    )

def send_import_process_percent(message,room):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room,
        {
            "type": "send_import_process_percent",
            "message": message,
        }
    )

def send_notification(message,room):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room,
        {
            "type": "send_notification",
            "message": message,
        }
    )