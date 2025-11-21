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

from utils.mixins import CompanyOwnershipRequiredMixin

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date,datetime

from .models import *
from .utils.black_list_person_utils import is_valid_black_list_person_data
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert

# Create your views here.

class UpdateThirdPersonStatusView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        
        if request.user.authorization.department != 'kredi_tahsis':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        obj = ThirdPerson.objects.select_related().filter(uuid = data.get('uuid')).first()
        obj.status = data.get('status') if data.get('status') == 'flagged' else 'need_document'
        obj.save()

        bank_activities = obj.bank_activities.select_related().all()
        for bank_activity in bank_activities:
            bank_activity.is_reliable_person = True if data.get('status') == 'cleared' else False
            bank_activity.third_person_status = data.get('status')
            bank_activity.save()

        return JsonResponse({'message': 'Durum değiştirildi!','status':'success'}, status=200)
    
class AddBlackListPersonView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        if request.user.authorization.department != 'kredi_tahsis':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)
        
        valid, response = is_valid_black_list_person_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        obj = BlackListPerson.objects.create(
            company = company,
            name = data.get('name'),
            tc_vkn_passport_no = data.get('tc_vkn_passport_no'),
            other_names = data.get('other_names'),
            nationality = data.get('nationality'),
            birthday = data.get('birthday'),
            organization = data.get('organization'),
            date_number = data.get('date_number'),
        )

        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
    
class ImportThirdPersonDocumentsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({'message': 'Yüklenecek dosya bulunamadı!','status':'error'}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Yetki hatası!.','status':'error'}, status=401)
        
        if request.user.authorization.department != 'operasyon':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        obj = ThirdPerson.objects.filter(uuid = data.get('uuid'), company = active_company.company).first()

        if not obj:
            return JsonResponse({'message': 'Bir hata oluştu!','status':'error'}, status=400)
        
        ThirdPersonDocument.objects.create(
            company = active_company.company,
            third_person = obj,
            label = file.name,
            file = file,
        )

        obj.status = 'cleared'
        obj.save()

        obj.bank_activities.update(
            is_reliable_person = True,
            third_person_status = 'cleared'
        )
        
        return JsonResponse({'message': 'Dosya başarıyla yüklendi!','status':'success'}, status=200)

