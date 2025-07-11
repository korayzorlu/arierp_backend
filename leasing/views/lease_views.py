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
from leasing.utils import is_valid_lease_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner
from contracts.models import Contract

import os
import json
import pandas as pd
from decimal import Decimal

# Create your views here.

class AddLeaseView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_lease_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        contract = Contract.objects.filter(uuid = data.get('contract')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Lease.objects.create(
            company = company,
            code = data.get('code'),
            contract = contract,
            type = data.get('kof'),
            vat = Decimal(str(data.get('quotation'))),
            activation_date = data.get('activation_date'),
            lease_status = data.get('lease_status'),
            currency = currency,
            musteri_baz_maliyet = Decimal(str(data.get('musteri_baz_maliyet'))),    
            vade =int( data.get('vade')),
            leasing_rate = Decimal(str(data.get('leasing_rate'))),
            irr = Decimal(str(data.get('irr'))),
            project_no = data.get('project_no'),
            status = status,
            leasing_type = data.get('leasing_type'),
            application_no = data.get('application_no'),
            is_last_project = data.get('is_last_project'),
            current_request = data.get('current_request'),
            finansman_kurum = data.get('finansman_kurum'),
            is_tufe = data.get('is_tufe'),
            is_musterek = data.get('is_musterek'),
            bbsn = data.get('bbsn'),
        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateLeaseView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_lease_data(data)
        if not valid:
            return response

        contract = Contract.objects.filter(uuid = data.get('contract')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Lease.objects.filter(uuid = data.get('uuid')).first()
        obj.code = data.get('code'),
        obj.contract = contract,
        obj.type = data.get('kof'),
        obj.vat = Decimal(str(data.get('quotation'))),
        obj.activation_date = data.get('activation_date'),
        obj.lease_status = data.get('lease_status'),
        obj.currency = currency,
        obj.musteri_baz_maliyet = Decimal(str(data.get('musteri_baz_maliyet'))),    
        obj.vade =int( data.get('vade')),
        obj.leasing_rate = Decimal(str(data.get('leasing_rate'))),
        obj.irr = Decimal(str(data.get('irr'))),
        obj.project_no = data.get('project_no'),
        obj.status = status,
        obj.leasing_type = data.get('leasing_type'),
        obj.application_no = data.get('application_no'),
        obj.is_last_project = data.get('is_last_project'),
        obj.current_request = data.get('current_request'),
        obj.finansman_kurum = data.get('finansman_kurum'),
        obj.is_tufe = data.get('is_tufe'),
        obj.is_musterek = data.get('is_musterek'),
        obj.bbsn = data.get('bbsn'),
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteLeaseView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Lease.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Lease.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        objs = Lease.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class LeasesTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "leases-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportLeasesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="leasing", model_name="Lease", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)



class UpdateLeaseflexAutomationLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Lease.objects.filter(uuid = uuid).first()
            obj.leaseflex_automation = data.get('select') or False
            obj.save()

        return JsonResponse({'message': 'Seçim değiştirildi!','status':'success'}, status=200)