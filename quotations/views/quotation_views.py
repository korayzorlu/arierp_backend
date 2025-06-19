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

from quotations.models import *
from quotations.utils import is_valid_quotation_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner
from contracts.models import Contract

import os
import json
import pandas as pd
from decimal import Decimal

# Create your views here.

class AddQuotationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_quotation_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        partner = Partner.objects.filter(uuid = data.get('partner')).first()
        quick_quotation = QuickQuotation.objects.filter(uuid = data.get('quick_quotation')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()

        obj = Quotation.objects.create(
            company = company,
            code = data.get('code'),
            partner = partner,
            quick_quotation = quick_quotation,
            status = status,
            currency = currency,
            kbm = data.get('kbm'),
            customer_representative = data.get('customer_representative'),
            kof = data.get('kof'),
            request_date = data.get('request_date'),
            rev_date = data.get('rev_date'),
            supplier = data.get('supplier'),
            project = data.get('project'),
        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateQuotationView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Quotation
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_quotation_data(data)
        if not valid:
            return response

        partner = Partner.objects.filter(uuid = data.get('partner')).first()
        quick_quotation = QuickQuotation.objects.filter(uuid = data.get('quick_quotation')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()

        obj = Quotation.objects.filter(uuid = data.get('uuid')).first()
        obj.code = data.get('code'),
        obj.partner = partner,
        obj.quick_quotation = quick_quotation,
        obj.status = status,
        obj.currency = currency,
        obj.kbm = data.get('kbm'),
        obj.customer_representative = data.get('customer_representative'),
        obj.kof = data.get('kof'),
        obj.request_date = data.get('request_date'),
        obj.rev_date = data.get('rev_date'),
        obj.supplier = data.get('supplier'),
        obj.project = data.get('project'),
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteQuotationView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Quotation

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Quotation.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteQuotationsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Quotation

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Quotation.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllQuotationsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Quotation

    def post(self, request, *args, **kwargs):
        objs = Quotation.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class QuotationsTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "quotations-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportQuotationsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="quotations", model_name="Quotation", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)