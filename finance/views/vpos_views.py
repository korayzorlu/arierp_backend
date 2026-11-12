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
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.utils.timezone import make_aware, is_aware
from dateutil import parser as dateutil_parser

from utils.mixins import CompanyOwnershipRequiredMixin

from finance.models import *
from finance.utils.vpos_utils import is_valid_vpos_transaction_data, add_vpos_transation,send_vpos_transation_to_leaseflex_test,compare_names,NameMatch,send_vpos_transation_to_leaseflex
from common.models import ImportProcess,ExportProcess,ExchangeRate
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_datetime,safe_decimal
from purchasing.models import PurchasePayment
from leasing.models import BankActivity
from underwriting.utils import check_third_person_status_vpos
from compliance.utils.third_person_utils import create_third_person_vpos
from finance.tasks import send_vpos_transation_to_leaseflex_test_task,send_vpos_transation_to_leaseflex_task

import json
import os
from django.utils.timezone import localtime

# Create your views here.

class AddVPosTransactionView(View):
    def post(self, request, *args, **kwargs):
        if request.body:
            data = json.loads(request.body)
        else:
            data = request.POST.dict() or request.GET.dict()
        
        valid, response = is_valid_vpos_transaction_data(data)
        if not valid:
            return response
        
        obj = add_vpos_transation(data)

        if not obj:
            return JsonResponse({'message': 'VPOS işlemi kaydedilemedi!','status':'error'}, status=400)

        if obj:
            third_person_result = compare_names(isim=data.get('Ad'), soyisim=data.get('SoyAd'), kart_sahibi=data.get('KartAdSoyad'))
            
            if third_person_result == NameMatch.REVIEW:
                #İnceleme gerekli: Ad ve Soyad ile Kart Ad Soyad benzer ama tam olarak eşleşmiyor.
                scan_result = check_third_person_status_vpos(data.get('KartAdSoyad'))
                create_third_person_vpos(obj,scan_result)
                obj.response_message = "Müşteri ismi ile kart sahibi ismi tam olarak eşleşmediği için 3. kişi kontrolü sonrası Leaseflex sistemine otomatik olarak aktarılacak."
                obj.save()
                return JsonResponse({'message': f'Başarıyla kaydedildi! Kart sahibi ile müşteri ismi uyuşmadığı için 3. kişi kontrolü sonrası Leaseflex sistemine otomatik olarak aktarılacak.','status':'success'}, status=200)
            elif third_person_result == NameMatch.NO_MATCH:
                #Farklı kişi: Ad ve Soyad ile Kart Ad Soyad eşleşmiyor.
                scan_result = check_third_person_status_vpos(data.get('KartAdSoyad'))
                create_third_person_vpos(obj,scan_result)
                obj.response_message = "Müşteri ismi ile kart sahibi ismi uyuşmadığı için 3. kişi kontrolü sonrası Leaseflex sistemine otomatik olarak aktarılacak."
                obj.save()
                return JsonResponse({'message': f'Başarıyla kaydedildi! Kart sahibi ile müşteri ismi uyuşmadığı için 3. kişi kontrolü sonrası Leaseflex sistemine otomatik olarak aktarılacak.','status':'success'}, status=200)

            sent, response_message = send_vpos_transation_to_leaseflex(obj.uuid)

            if not sent:
                obj.status = Statuses.REJECTED
                obj.last_error = response_message
                obj.save()
                return JsonResponse({'message': f"Leaseflex'ten gelen hata: {response_message}",'status':'error'}, status=400)

            obj.status = Statuses.SENT
            obj.response_message = response_message
            obj.save()

        return JsonResponse({'message': f'Başarıyla kaydedildi! Leaseflex mesajı: {response_message}','status':'success'}, status=200)
