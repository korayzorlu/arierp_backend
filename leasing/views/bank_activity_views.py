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
from common.utils.common_utils import parse_amount
from partners.models import Partner
from contracts.models import Contract

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date,datetime

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
        exporter = BaseExporter(
            user_id=request.user.id,
            app="leasing",
            model_name="BankActivity",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-banka-hareketleri.xlsx",
            export_url="/leasing/bank_activities_excel"
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class BankActivitiesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "bank_activities", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-banka-hareketleri.xlsx")
      
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

        parsed_amount = parse_amount(data.get('amount'))

        obj.processed_amount = parsed_amount
        obj.save()

        return JsonResponse({'message': 'Tutar değiştirildi!','status':'success'}, status=200)
    
class UpdateBankActivityLeasesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        partner = Partner.objects.select_related().filter(uuid = data.get('uuid')).first()
        bank_activity = BankActivity.objects.select_related().filter(uuid = data.get('bank_activity_uuid')).first()
   
        bank_activity_leases = bank_activity.bank_activity_bank_acitivity_leases.all()
        
        if bank_activity_leases:
            for bank_activity_lease in bank_activity_leases:
                current_lease = bank_activity_lease.lease
                current_lease.leaseflex_automation = False
                current_lease.processed_amount = Decimal("0")
                current_lease.save()
            bank_activity_leases.delete()

        leases = Lease.objects.filter(
            Q(contract__partner__uuid = partner.uuid) &
            (
                Q(lease_status = "aktiflestirildi") |
                Q(lease_status = "planlandi") |
                Q(lease_status = "durduruldu")
            ) 
        ).order_by('contract_id', '-activation_date').distinct('contract_id')

        if leases:
            for lease in leases:
                bank_activity_lease = BankActivityLease.objects.create(
                    company = bank_activity.company,
                    bank_activity = bank_activity,
                    lease = lease
                )

                processed_amount = bank_activity.amount
                
                installments = lease.lease_installments.all()
                total_overdue_amount = Decimal("0")
                for installment in installments:
                    total_overdue_amount += installment.overdue_amount
                total_overdue_amount = total_overdue_amount - lease.processed_amount #test
                if total_overdue_amount > 0:
                    #bank_activity_lease.leaseflex_automation = True
                    if processed_amount > 0:
                        if total_overdue_amount <= processed_amount:
                            bank_activity_lease.processed_amount = total_overdue_amount
                            processed_amount -= total_overdue_amount
                        else:
                            bank_activity_lease.processed_amount = processed_amount
                            processed_amount = 0
                    # else:
                    #     bank_activity_lease.leaseflex_automation = False
                    bank_activity_lease.save()
                if partner.tc_vkn_no != bank_activity.tc_vkn_no:
                        bank_activity_lease.is_third_person = True
                        bank_activity_lease.save()
                bank_activity_leases = lease.lease_bank_acitivity_leases.select_related().all()
                total_bank_activity_leases_processed_amount = Decimal("0")
                for item in bank_activity_leases:
                    total_bank_activity_leases_processed_amount += item.processed_amount
                lease.processed_amount = total_bank_activity_leases_processed_amount
                lease.save()

        return JsonResponse({'message': 'Tutar değiştirildi!','status':'success'}, status=200)