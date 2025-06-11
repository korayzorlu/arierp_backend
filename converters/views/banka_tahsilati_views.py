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

from converters.models import *
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert

import os
import json
import pandas as pd

# Create your views here.
    
class ImportBankaTahsilatlariView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="converters", model_name="BankaTahsilati", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)

class DeleteBankaTahsilatiView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankaTahsilati

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = BankaTahsilati.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    

class DeleteBankaTahsilatlariView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankaTahsilati

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = BankaTahsilati.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllBankaTahsilatlariView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = BankaTahsilati

    def post(self, request, *args, **kwargs):
        objs = BankaTahsilati.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
 