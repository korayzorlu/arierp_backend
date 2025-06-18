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

from .models import *
from .utils import is_valid_contract_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner

import os
import json
import pandas as pd

# Create your views here.

class AddContractView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_contract_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        partner = Partner.objects.filter(uuid = data.get('partner')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Contract.objects.create(
            company = company,
            code = data.get('code'),
            partner = partner,
            kof = data.get('kof'),
            quotation = data.get('quotation'),
            committe = data.get('committe'),
            credit_type = data.get('credit_type'),
            customer_representative = data.get('customer_representative'),
            supplier = data.get('supplier'),
            project = data.get('project'),
            status = status,
            mkk_tesciline_gonderilecek_mi = data.get('mkk_tesciline_gonderilecek_mi'),
            kof_tan_sozlesmeye_aktarim_tarihi = data.get('kof_tan_sozlesmeye_aktarim_tarihi'),
            lop_open_date = data.get('lop_open_date'),
        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateContractView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Contract
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_contract_data(data)
        if not valid:
            return response

        partner = Partner.objects.filter(uuid = data.get('partner')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Contract.objects.filter(uuid = data.get('uuid')).first()
        obj.code = data.get('code')
        obj.partner = partner
        obj.kof = data.get('kof')
        obj.quotation = data.get('quotation')
        obj.committe = data.get('committe')
        obj.credit_type = data.get('credit_type')
        obj.customer_representative = data.get('customer_representative')
        obj.supplier = data.get('supplier')
        obj.project = data.get('project')
        obj.status = status
        obj.mkk_tesciline_gonderilecek_mi = data.get('mkk_tesciline_gonderilecek_mi')
        obj.kof_tan_sozlesmeye_aktarim_tarihi = data.get('kof_tan_sozlesmeye_aktarim_tarihi')
        obj.lop_open_date = data.get('lop_open_date')
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteContractView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Contract

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Contract.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteContractsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Contract

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Contract.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllContractsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Contract

    def post(self, request, *args, **kwargs):
        objs = Contract.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class ContractsTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "contracts-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportContractsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="contracts", model_name="Contract", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)