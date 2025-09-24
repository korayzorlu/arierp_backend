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
from django.utils.timezone import make_aware

from utils.mixins import CompanyOwnershipRequiredMixin

from .models import *
from contracts.models import Contract
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_amount
from common.models import ImportProcess,ExportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter


import json
import os
from decimal import Decimal
from datetime import date,datetime

# Create your views here.

class AddPartnerAdvanceActivityView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        partner = Partner.objects.select_related().filter(uuid = data['uuid']).first()

        PartnerAdvanceActivity.objects.create(
            company = self.request.user.user_companies.filter(is_active=True).first().company,
            partner = partner,
            # bank_code = finmaks_transaction.bank_code,
            # bank_branch_code = finmaks_transaction.branch_code,
            # bank_account_no = finmaks_transaction.bank_account.account_no,
            # cross_bank_code = finmaks_transaction.bank_code,
            # cross_bank_branch_code = finmaks_transaction.transaction_branch_code,
            # cross_bank_account_no = finmaks_transaction.sender_iban,
            # process_code = finmaks_transaction.transaction_id,
            # credit_or_debit = "C" if finmaks_transaction.debit == "+" else "D",
            # kontrat_no = finmaks_transaction.receipt_number,
            # process_date_date = finmaks_transaction.transaction_date.date(),
            #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
            # amount = finmaks_transaction.amount,
            # currency = finmaks_transaction.bank_account.currency,
            name = partner.name,
            # description = finmaks_transaction.explanation_field,
            tc_vkn_no = partner.tc_vkn_no,
        )

        return JsonResponse({'message': 'Başarıyla Gönderildi!','status':'success'}, status=200)
    
class UpdateLeaseflexAutomationPartnerAdvanceActivityLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = PartnerAdvanceActivityLease.objects.filter(uuid = uuid).first()

            obj.leaseflex_automation = data.get('select') or False
            obj.save()

        return JsonResponse({'message': 'Seçim değiştirildi!','status':'success'}, status=200)
    
class UpdatePartnerAdvanceActivityLeaseProcessedAmountView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = PartnerAdvanceActivityLease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = PartnerAdvanceActivityLease.objects.filter(uuid = data.get('uuid')).first()

        parsed_amount = parse_amount(data.get('amount'))

        obj.processed_amount = parsed_amount
        obj.save()

        return JsonResponse({'message': 'Tutar değiştirildi!','status':'success'}, status=200)
    
class UpdatePartnerAdvanceActivityLeasesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        partner = Partner.objects.select_related().filter(uuid = data.get('uuid')).first()
        partner_advance_activity = PartnerAdvanceActivity.objects.select_related().filter(uuid = data.get('partner_advance_activity_uuid')).first()
   
        partner_advance_activity_leases = partner_advance_activity.partner_advance_activity_partner_advance_activity_leases.all()
        partner_advance_activity_leases.delete()

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
                partner_advance_activity_lease = PartnerAdvanceActivityLease.objects.create(
                    company = partner_advance_activity.company,
                    partner_advance_activity = partner_advance_activity,
                    lease = lease
                )

        return JsonResponse({'message': 'Kaydedildi!','status':'success'}, status=200)
    
class ExportPartnerAdvanceActivitiesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        exporter = BaseExporter(
            user_id=request.user.id,
            app="operation",
            model_name="PartnerAdvanceActivity",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-müşteri-avansları.xlsx",
            export_url="/operation/partner_advance_activities_excel"
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class PartnerAdvanceActivitiesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "operation", "partner_advance_activities", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-müşteri-avansları.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    

class UpdateContractOperationStatusView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Contract

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            contract = Contract.objects.select_related().filter(uuid = uuid).first()

            if contract:
                contract.operation_status = data.get('operationStatus') or contract.operation_status
                contract.save()

        return JsonResponse({'message': 'Kaydedildi!','status':'success'}, status=200)