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
from leasing.utils.lease_utils import get_future_payments
from contracts.models import TerminationWarningNotice

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime
from docxtpl import DocxTemplate
import io, zipfile

# Create your views here.

class ExportToTerminatedRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToTerminatedRiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler-sms.xlsx",
            export_url="/risk/to_terminated_risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToTerminatedRiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))


class ExportToTerminatedRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToTerminatedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx",
            export_url="/risk/to_terminated_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToTerminatedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))

class CreateTerminationWarningNoticeStatusView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        lease = Lease.objects.select_related().filter(uuid = data.get('uuid')).first()

        if lease:
            # kapsamlı ihtar model işlemleri
            if not TerminationWarningNotice.objects.filter(contract = lease.contract).exists():
                obj = TerminationWarningNotice.objects.create(
                    company = lease.company,
                    contract = lease.contract,
                )
            else:
                obj = TerminationWarningNotice.objects.filter(contract = lease.contract).first()

            # word işlemleri
            file_name = lease.contract.code.replace("/","-")
            doc = DocxTemplate(f"files/fesih-ihtar.docx")

            def format_currency(value):
                    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
            
            if lease.contract.partner.is_commercial:
                if lease.contract.partner.tc_vkn_no and len(lease.contract.partner.tc_vkn_no) > 0:
                    tc_vkn_no = lease.contract.partner.tc_vkn_no
                elif lease.contract.partner.vat_no and len(lease.contract.partner.vat_no) > 0:
                    tc_vkn_no = lease.contract.partner.vat_no
                else:
                    tc_vkn_no = ''
            else:
                tc_vkn_no = lease.contract.partner.tc_vkn_no if lease.contract.partner.tc_vkn_no else ''

            context = {
                "isim": lease.contract.partner.name,
                "tc_vkn_no": tc_vkn_no,
                "adres": lease.contract.partner.address,
                "sozlesme_tarih": lease.signature_date.strftime('%d.%m.%Y') if lease.signature_date else '',
                "sozlesme_no": lease.contract.code,
                "odenen_tutar": format_currency(obj.paid_amount),
                "kesinti_tutar": format_currency(obj.deduction_amount),
                "toplam_tutar": format_currency(obj.paid_amount - obj.deduction_amount),
            }
            doc.render(context)

            files_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{file_name}.docx")
            doc.save(files_path)

        if files_path:
            return FileResponse(open(files_path, 'rb'), as_attachment=True)
        
        return JsonResponse({'message': 'Dosya bulunamadı!','status':'error'}, status=400)

class GetTerminationWarningNoticeView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuid = data.get('uuid')

        lease = Lease.objects.select_related().filter(uuid = uuid).first()

        file_name = lease.contract.code.replace("/","-")
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{file_name}.docx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)
        
        return FileResponse(open(file_path, 'rb'))