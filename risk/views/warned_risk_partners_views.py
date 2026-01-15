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

from utils.mixins import CompanyOwnershipRequiredMixin

from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.models import ExportProcess
from leasing.models import Lease

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime
from docxtpl import DocxTemplate
import io, zipfile

# Create your views here.

class ExportWarnedRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="WarnedRiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler-sms.xlsx",
            export_url="/risk/warned_risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarnedRiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))


class ExportWarnedRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="WarnedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx",
            export_url="/risk/warned_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarnedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))

class UpdateWarningNoticeStatusView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        files = []
        

        for uuid in uuids:
            lease = Lease.objects.select_related().filter(uuid = uuid).first()

            if lease:
                lease.warning_notice_status = 'kapsamli_ihtar'
                lease.save()

                # word işlemleri
                file_name = lease.contract.code
                doc = DocxTemplate(f"files/ihtar-{'ticari' if lease.contract.partner.is_commercial else 'tuketici'}.docx")
                context = {
                    "tarih": datetime.today().strftime('%d.%m.%Y'),
                    "isim": lease.contract.partner.name,
                    "adres": lease.contract.partner.address,
                    "sozlesme_tarih": lease.activation_date.strftime('%d.%m.%Y') if lease.activation_date else '',
                }
                doc.render(context)

                files_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{file_name}.docx")
                doc.save(files_path)

                files.append(files_path)

        # zip işlemleri
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w") as zip_file:
            for path in files:
                zip_file.write(path, arcname=path.split('/')[-1])

        buffer.seek(0)
    
        return FileResponse(buffer)

        # return JsonResponse({'message': 'Başarıyla gönderildi!','status':'success'}, status=200)