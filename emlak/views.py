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
from emlak.utils import make_whatsapp_message,send_wb_message,format_date_tr

import json
import time

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

class SendWhatsappMessageView(LoginRequiredMixin,View):
    model = WhatsappMessage

    def post(self, request, *args, **kwargs):
        from operation.api.views import UntitleDeedLeaseList
        from rest_framework.request import Request
        data = json.loads(request.body)
        
        # if request.user.authorization.department != 'operasyonn':
        #     return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)

        print(data)

        objs = WhatsappMessage.objects.filter(uuid__in=data.get('uuids', []))

        for obj in objs:
            print(obj.real_estate_agent.name)
            print(obj.real_estate_agent.phone_number_1)

            params = {
                "name": obj.real_estate_agent.name,
                "phone_number": obj.real_estate_agent.phone_number_1,
                "meet_date": format_date_tr(obj.meet_date) if obj.meet_date else "",
                "online_meet_date": format_date_tr(obj.online_meet_date) if obj.online_meet_date else ""
            }

            response = send_wb_message(params)

            if response.status_code == 200:
                obj.is_sent = True
                obj.save()

            time.sleep(1.5)

        return JsonResponse({'message': 'Mesaj gönderimi başlatıldı...','status':'success'}, status=200)