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

from communication.models import SMS
from communication.utils.sms_utils import send_sms_with_turatel,check_sms_status
from communication.tasks import send_sms
from partners.models import Partner

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

class SendSMSView(LoginRequiredMixin,View):
    model = SMS

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        if request.user.authorization.department != 'kredi_risk_izlemeee':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)
        send_sms.delay(data)

        return JsonResponse({'message': 'SMS gönderimi başlatıldı. Mesajların iletim durumunu iletişim sütununda yer alan mesaj butonlarından takip edebilirsiniz.','status':'success'}, status=200)
    
class CheckSMSView(LoginRequiredMixin,View):
    model = SMS

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        partner_obj = Partner.objects.filter(uuid=data.get("uuid")).first()
        message_obj = partner_obj.partner_smss.filter().order_by("-created_date").first()
        if message_obj:
            check_sms_status({"message_id_list": [message_obj.message_id]})

        return JsonResponse({},status=200)