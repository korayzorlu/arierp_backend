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
from contracts.models import ComprehensiveWarningNotice

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
                file_name = lease.contract.code.replace("/","-")
                doc = DocxTemplate(f"files/ihtar-{'ticari' if lease.contract.partner.is_commercial else 'tuketici'}.docx")
         
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

                gecikme_bakiye = lease.overdue_amount
                masraf_bakiye = (gecikme_bakiye / Decimal('100')) * Decimal('15')
                toplam_borc_bakiye = gecikme_bakiye + masraf_bakiye
                gelecek_bakiye = get_future_payments(lease.lease_id)
                toplam_bakiye = toplam_borc_bakiye + gelecek_bakiye

                context = {
                    "tarih": datetime.today().strftime('%d.%m.%Y'),
                    "isim": lease.contract.partner.name,
                    "tc_vkn_no": tc_vkn_no,
                    "adres": lease.contract.partner.address,
                    "sozlesme_tarih": lease.activation_date.strftime('%d.%m.%Y') if lease.activation_date else '',
                    "sozlesme_no": lease.contract.code,
                    "il": f"{lease.city} ili, " if lease.city else '',
                    "ilce": f"{lease.district} ilçesi, " if lease.district else '',
                    "ada": f"{lease.island} ada, " if lease.island else '',
                    "parsel": f"{lease.parcel} parsel, " if lease.parcel else '',
                    "blok": f"{lease.block} blok, " if lease.block else '',
                    "bagimsiz_bolum": f"{lease.unit} numaralı bağımsız bölüm " if lease.unit else '',
                    "gecikme_bakiye": format_currency(gecikme_bakiye),
                    "masraf_bakiye": format_currency(masraf_bakiye),
                    "toplam_borc_bakiye": format_currency(toplam_borc_bakiye),
                    "gelecek_bakiye": format_currency(gelecek_bakiye),
                    "toplam_bakiye": format_currency(toplam_bakiye),
                }
                doc.render(context)

                files_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{file_name}.docx")
                doc.save(files_path)

                files.append(files_path)

                # kapsamlı ihtar model işlemleri
                if not ComprehensiveWarningNotice.objects.filter(contract = lease.contract).exists():
                    ComprehensiveWarningNotice.objects.create(
                        company = lease.company,
                        contract = lease.contract,
                        debit_amount = toplam_bakiye,
                    )

        # zip işlemleri
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w") as zip_file:
            for path in files:
                zip_file.write(path, arcname=path.split('/')[-1])

        buffer.seek(0)
    
        return FileResponse(buffer)

        # return JsonResponse({'message': 'Başarıyla gönderildi!','status':'success'}, status=200)

class GetWarningNoticeView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuid = data.get('uuid')

        lease = Lease.objects.select_related().filter(uuid = uuid).first()

        file_name = lease.contract.code.replace("/","-")
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{file_name}.docx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)
        
        return FileResponse(open(file_path, 'rb'))