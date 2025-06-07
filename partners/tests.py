from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from common.utils.websocket_utils import send_alert,fetch_import_processes

import json

# Create your views here.

class ExampleView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        #send_alert({"message":f"This is test alert!","status":"success"},room=f"private_{request.user.id}")
        fetch_import_processes({"status":"in_progress","model":"Partner","activeCompany": {"id":1}},room=f"private_{request.user.id}")

        return JsonResponse({'message': 'This is a test','status':'info'}, status=200)
 