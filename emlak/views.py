from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utils.mixins import CompanyOwnershipRequiredMixin

from .models import *
from .utils import is_valid_whatsapp_message_data
from emlak.utils import make_whatsapp_message

import json

class MakeWhatsappMessageView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        company = request.user.user_companies.filter(is_active = True).first().company

        data.update({"company": company})

        valid, response = is_valid_whatsapp_message_data(data)
        if not valid:
            return response
        
        make_whatsapp_message(data)

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class DeleteWhatsappMessageView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        for uuid in data.get('uuids', []):
            WhatsappMessage.objects.filter(uuid=uuid).delete()

        return JsonResponse({'message': 'Başarıyla silindi!','status':'success'}, status=200)