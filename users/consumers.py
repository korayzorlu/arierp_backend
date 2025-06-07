from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from django.core.exceptions import ValidationError

import json

from .models import User

import django
django.setup()

class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]  # Kullanıcıyı scope içinden al
        if user.is_anonymous:  # Kullanıcı giriş yapmamışsa bağlantıyı reddet
            await self.close()
            return

        self.room_name = str(user.uuid)
        self.room_group_name = f"private_{self.room_name}"
        self.group_name = 'public_room'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        type = data.get('type')

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({ 'type': event['type'], 'message': event['message'] }))

    async def send_alert(self, event):
        await self.send(text_data=json.dumps({ 'type': event['type'], 'message': event['message'] }))
    async def send_percent(self, event):
        await self.send(text_data=json.dumps({ 'type': event['type'], 'message': event['message'] }))
    async def send_import_process_percent(self, event):
        await self.send(text_data=json.dumps({ 'type': event['type'], 'message': event['message'] }))
    async def fetch_import_processes(self, event):
        await self.send(text_data=json.dumps({ 'type': event['type'], 'message': event['message'] }))