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

from partners.models import *
from partners.tasks import importPartners
from partners.utils import is_valid_partner_data, get_partner_types,is_valid_sector_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert

import os
import json
import pandas as pd

# Create your views here.

class AddSectorView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_sector_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        obj = Sector.objects.create(
            company = company,
            code = data.get('code'),
            name = data.get('name'),
            main_sector_code = data.get('mainSectorCode'),
            match_code = data.get('matchCode'),
            kkbmb_sector_code = data.get('kkbmbSectorCode')
        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateSectorView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Sector
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        print(data)
        valid, response = is_valid_sector_data(data)
        if not valid:
            return response

        obj = Sector.objects.filter(uuid = data.get('uuid')).first()
        obj.code = data.get('code')
        obj.name = data.get('name')
        obj.main_sector_code = data.get('mainSectorCode')
        obj.match_code = data.get('matchCode')
        obj.kkbmb_sector_code = data.get('kkbmbSectorCode')
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteSectorView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Sector

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Sector.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteSectorsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Sector

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Sector.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllSectorsView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Sector

    def post(self, request, *args, **kwargs):
        objs = Sector.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class SectorsTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "sectors-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportSectorsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="partners", model_name="Sector", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)