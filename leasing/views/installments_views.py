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
from django.utils.timezone import localtime

from utils.mixins import CompanyOwnershipRequiredMixin

from leasing.models import *
from leasing.utils.common_utils import is_valid_installment_data,is_valid_installment_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner
from contracts.models import Contract
from risk.utils.exchanged_leases_utils import compute_tufe_endeks

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date

# Create your views here.

class AddInstallmentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_installment_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        lease = Lease.objects.filter(uuid = data.get('lease')).first()

        obj = Installment.objects.create(
            company = company,
            lease = lease,
            payment_date = data.get('payment_date'),
            vat = Decimal(str(data.get('vat'))),
            amount = Decimal(str(data.get('amount'))),
            paid = Decimal(str(data.get('paid'))),
            priciple = Decimal(str(data.get('priciple'))),
            interest = Decimal(str(data.get('interest'))),
            sequency = int(data.get('sequency')),

        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateInstallmentView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Installment
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_installment_data(data)
        if not valid:
            return response

        lease = Lease.objects.filter(uuid = data.get('lease')).first()

        obj = Installment.objects.filter(uuid = data.get('uuid')).first()
        obj.lease = lease
        obj.payment_date = data.get('payment_date')
        obj.vat = Decimal(str(data.get('vat')))
        obj.amount = Decimal(str(data.get('amount')))
        obj.paid = Decimal(str(data.get('paid')))
        obj.priciple = Decimal(str(data.get('priciple')))
        obj.interest = Decimal(str(data.get('interest')))
        obj.sequency = int(data.get('sequency'))
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteInstallmentView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Installment

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Installment.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteInstallmentsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Installment

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Installment.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllInstallmentsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Installment

    def post(self, request, *args, **kwargs):
        objs = Installment.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class InstallmentsTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "leases-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportInstallmentsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="leasing", model_name="Installment", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)
    
class InstallmentInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        lease = Lease.objects.filter(uuid = data.get('lease_id')).first()
        compute_tufe_endeks(lease)
        
        if data.get('lease_code'):
            objs = Installment.objects.select_related('lease','lease__contract','lease__currency').filter(lease__code = str(data.get('lease_code'))).order_by("sequency")
        else:
            objs = Installment.objects.select_related('lease','lease__contract','lease__currency').filter(lease__uuid = str(data.get('lease_id'))).order_by("sequency")
    
        if not objs:
            return JsonResponse({'installment':[]}, status=200)
        
        tts = lease.lease_trade_transactions.filter(amount_type = '0', posting_group_name = 'Kira').order_by("due_date","record_date")
        lease_tts = [
            {
                'id': tt.uuid,
                'amount': tt.amount,
                'applied_amount' : Decimal('0.00'),
                'remaining_amount' : tt.amount
            }
            for tt in tts
        ]

        payment_tts = [tt for tt in tts if tt.amount_type == '0']

        # Remaining balance per TT — used for carryover allocation
        tt_remaining = {tt.id: tt.amount for tt in payment_tts}

        installments_list = list(objs)
        inst_trans_map = {}

        for inst in installments_list:
            applied = []

            if not inst.payment_date:
                inst_trans_map[inst.id] = applied
                continue

            still_needed = inst.amount

            # First consume any carryover from TTs whose date precedes this installment
            for tt in payment_tts:
                if still_needed <= 0:
                    break
                if not tt.due_date:
                    continue
                tt_date = localtime(tt.due_date).date()
                avail = tt_remaining[tt.id]
                if avail > 0 and (
                    tt_date.year < inst.payment_date.year or
                    (tt_date.year == inst.payment_date.year and tt_date.month < inst.payment_date.month)
                ):
                    apply = min(avail, still_needed)
                    applied.append({'tt': tt, 'applied': apply})
                    tt_remaining[tt.id] -= apply
                    still_needed -= apply

            # Then match TTs whose due_date falls in the same month/year as this installment
            for tt in payment_tts:
                if still_needed <= 0:
                    break
                if not tt.due_date:
                    continue
                tt_date = localtime(tt.due_date).date()
                avail = tt_remaining[tt.id]
                if (
                    avail > 0
                    and tt_date.year == inst.payment_date.year
                    and tt_date.month == inst.payment_date.month
                ):
                    apply = min(avail, still_needed)
                    applied.append({'tt': tt, 'applied': apply})
                    tt_remaining[tt.id] -= apply
                    still_needed -= apply

            inst_trans_map[inst.id] = applied

        installment_data = [
            {
                'id': obj.uuid,
                'project':obj.lease.contract.project if obj.lease.contract else "",
                'lease':obj.lease.code if obj.lease else "",
                'sequency': obj.sequency,
                'vat': obj.vat,
                'vat_amount': obj.vat_amount,
                'payment': obj.payment,
                'amount' : obj.amount,
                'payment_date':obj.payment_date.strftime('%d.%m.%Y') if obj.payment_date else "",
                'currency':obj.lease.currency.code if obj.lease.currency else "",
                'type': obj.type,
                'type_display': obj.get_type_display() if obj.type else "",
                'transactions': [
                    {
                        'id': str(item['tt'].uuid),
                        'amount': item['tt'].amount,
                        'applied_amount': item['applied'],
                        'remaining_amount': item['tt'].amount - item['applied'],
                        'due_date': localtime(item['tt'].due_date).strftime('%d.%m.%Y') if item['tt'].due_date else None,
                        'description': item['tt'].description,
                        'document_no': item['tt'].document_no,
                        'currency': item['tt'].currency.code if item['tt'].currency else "",
                    }
                    for item in inst_trans_map.get(obj.id, [])
                ],
                'islenen_tutar': sum(t['applied'] for t in inst_trans_map.get(obj.id, [])),
                'bakiye': obj.amount - sum(t['applied'] for t in inst_trans_map.get(obj.id, []))
            }
            for obj in installments_list
        ]



        return JsonResponse({'installment':installment_data}, status=200)