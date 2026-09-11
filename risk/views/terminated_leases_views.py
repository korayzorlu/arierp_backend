from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

from utils.mixins import CompanyOwnershipRequiredMixin

from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.models import ExportProcess
from leasing.models import Lease,Installment
from leasing.utils.lease_utils import get_future_payments
from contracts.models import TerminationWarningNotice, CommitteeForm,WarningNotice
from partners.models import Partner
from risk.utils.filter_utils import cancellation_warning_notice_exists

import os
import json
import pandas as pd
from collections import Counter
from decimal import Decimal
from datetime import datetime
from docxtpl import DocxTemplate
import io, zipfile
from copy import deepcopy
from docx.oxml.ns import qn

class ExportTerminatedLeasesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="TerminatedLease",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilenler.xlsx",
            export_url="/risk/terminated_leases_excel"
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class TerminatedLeasesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "terminated_leases", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilenler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))

class UpdateTerminatedDateView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Lease.objects.filter(uuid = data.get('id')).first()
        
        if obj and data.get('terminated_date'):
            obj.terminated_date = datetime.strptime(data.get('terminated_date'), '%d.%m.%Y').date()
            obj.save()
            return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
        else:
            return JsonResponse({'message': 'Bir hata oluştu!','status':'error'}, status=400)