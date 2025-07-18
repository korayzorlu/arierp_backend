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

from leasing.models import *
from leasing.utils import is_valid_installment_data,is_valid_installment_data
from common.models import ImportProcess,ExportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner
from contracts.models import Contract

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date

# Create your views here.
    
class DeleteBankActivityView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankActivity

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = BankActivity.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteBankActivitiesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankActivity

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = BankActivity.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllBankActivitiesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankActivity

    def post(self, request, *args, **kwargs):
        objs = BankActivity.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class BankActivitiesTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "leases-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportBankActivitiesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="leasing", model_name="BankActivity", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)
    
class ExportBankActivitiesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        exporter = BaseExporter(user_id=request.user.id, app="leasing", model_name="BankActivity")

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class BankActivitiesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "bank_activities", "documents","banka-hareketleri.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class UpdateLeaseflexAutomationBankActivityLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = BankActivityLease.objects.filter(uuid = uuid).first()
            print(obj)
            obj.leaseflex_automation = data.get('select') or False
            obj.save()

        return JsonResponse({'message': 'Seçim değiştirildi!','status':'success'}, status=200)
    
class UpdateBankActivityLeaseProcessedAmountView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankActivityLease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = BankActivityLease.objects.filter(uuid = data.get('uuid')).first()
        obj.processed_amount = Decimal(str(data.get('amount')).replace(",","."))
        obj.save()

        return JsonResponse({'message': 'Tutar değiştirildi!','status':'success'}, status=200)