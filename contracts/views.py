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
from .utils.common_utils import is_valid_contract_data
from common.models import ImportProcess,ExportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from partners.models import Partner
from companies.models import UserCompany

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from docxtpl import DocxTemplate

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
    
class WarningNoticeInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        contract = data.get('contract')

        active_company_uuid = data.get('active_company')
        active_company = UserCompany.objects.select_related("company").filter(uuid = active_company_uuid).first()
        
        obj = WarningNotice.objects.filter(company = active_company.company, contract__code = contract, state__in=['Yeni', 'Geçerli']).first()

        if not obj:
            return JsonResponse({'message' : 'Aradığınız veri bulunamadı!','status':'error'}, status=400)
        
        warning_notice_data = {
            'partner': obj.contract.partner.name if obj.contract else "",
            'contract': obj.contract.code if obj.contract else "",
            'currency': obj.contract.currency.code if obj.contract else "",
            'document_id': obj.document_id,
            'risk_id': obj.risk_id,
            'customer_id': obj.customer_id,
            'debit_amount': obj.debit_amount,
            'daily_wages_date': obj.daily_wages_date.strftime('%d.%m.%Y') if obj.daily_wages_date else "",
            'process_start_date': obj.process_start_date.strftime('%d.%m.%Y') if obj.process_start_date else "",
            'service_date': obj.service_date.strftime('%d.%m.%Y') if obj.service_date else "",
            'official_cancellation_date': obj.official_cancellation_date.strftime('%d.%m.%Y') if obj.official_cancellation_date else "",
            'paid': obj.paid,
            'diff': obj.diff,
            'state': obj.state,
            'approval_state': obj.approval_state,
            'termination_days': (obj.official_cancellation_date - obj.service_date).days if obj.official_cancellation_date and obj.service_date else "",
        }

        return JsonResponse({'warning_notice':warning_notice_data}, status=200)

class ComprehensiveWarningNoticeInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        contract = data.get('contract')

        active_company_uuid = data.get('active_company')
        active_company = UserCompany.objects.select_related("company").filter(uuid = active_company_uuid).first()
        
        obj = ComprehensiveWarningNotice.objects.filter(company = active_company.company, contract__code = contract).first()

        if not obj:
            return JsonResponse({'message' : 'Aradığınız veri bulunamadı!','status':'error'}, status=400)
        
        comprehensive_warning_notice_data = {
            'uuid': obj.uuid,
            'partner': obj.contract.partner.name if obj.contract else "",
            'contract': obj.contract.code if obj.contract else "",
            'currency': obj.contract.currency.code if obj.contract else "",
            'debit_amount': obj.debit_amount,
            'process_start_date': obj.process_start_date.strftime('%d.%m.%Y') if obj.process_start_date else "",
            'service_date': obj.service_date.strftime('%d.%m.%Y') if obj.service_date else "",
            'official_cancellation_date': obj.official_cancellation_date.strftime('%d.%m.%Y') if obj.official_cancellation_date else "",
            'termination_days': (obj.official_cancellation_date - obj.service_date).days if obj.official_cancellation_date and obj.service_date else "",
            'days_remaining': (obj.official_cancellation_date - datetime.today().date()).days if obj.official_cancellation_date else "",
        }

        return JsonResponse({'comprehensive_warning_notice':comprehensive_warning_notice_data}, status=200)
    
class UpdateComprehensiveWarningNoticeView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = ComprehensiveWarningNotice
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        obj = ComprehensiveWarningNotice.objects.filter(uuid = data.get('uuid')).first()

        if not obj:
            return JsonResponse({'message': 'Bir sorun oluştu!','status':'error'}, status=400)
        
        service_date_str = data.get('service_date')
        if service_date_str:
            try:
                obj.service_date = datetime.strptime(service_date_str, '%d.%m.%Y').date()
                obj.official_cancellation_date = obj.service_date + timedelta(days=60)
            except ValueError:
                return JsonResponse({'message': 'Tarih formatı geçersiz! Lütfen GG.AA.YYYY formatında giriniz.','status':'error'}, status=400)
        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class TerminationWarningNoticeInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        contract = data.get('contract')

        active_company_uuid = data.get('active_company')
        active_company = UserCompany.objects.select_related("company").filter(uuid = active_company_uuid).first()
        
        obj = TerminationWarningNotice.objects.filter(company = active_company.company, contract__code = contract).first()

        if not obj:
            return JsonResponse({'message' : 'Aradığınız veri bulunamadı!','status':'error'}, status=400)
        
        termination_warning_notice_data = {
            'uuid': obj.uuid,
            'partner': obj.contract.partner.name if obj.contract else "",
            'contract': obj.contract.code if obj.contract else "",
            'currency': obj.contract.currency.code if obj.contract else "",
            'paid_amount': f"{float(obj.paid_amount):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'deduction_amount': f"{float(obj.deduction_amount):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'total_amount': f"{float(obj.paid_amount - obj.deduction_amount):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        }

        return JsonResponse({'termination_warning_notice':termination_warning_notice_data}, status=200)
    
class UpdateTerminationWarningNoticeView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = TerminationWarningNotice
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        obj = TerminationWarningNotice.objects.filter(uuid = data.get('uuid')).first()

        if not obj:
            return JsonResponse({'message': 'Bir sorun oluştu!','status':'error'}, status=400)
        
        paid_amount_str = data.get('paid_amount', '0,00').replace('.', '').replace(',', '.')
        paid_amount = Decimal(str(paid_amount_str))

        deduction_amount_str = data.get('deduction_amount', '0,00').replace('.', '').replace(',', '.')
        deduction_amount = Decimal(str(deduction_amount_str))

        try:
            obj.paid_amount = paid_amount
            obj.deduction_amount = deduction_amount
        except ValueError:
            return JsonResponse({'message': 'Bir hata oluştu!','status':'error'}, status=400)
        
        obj.save()

        # word işlemleri
        lease = obj.contract.contract_leases.filter(is_last_project=True).first()
        file_name = obj.contract.code.replace("/","-")
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
        # word işlemleri - end

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class ExportContractPaymentsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        exporter = BaseExporter(
            user_id=request.user.id,
            app="contracts",
            model_name="ContractPayment",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-tahsilatlar.xlsx",
            export_url="/contracts/contract_payments_excel",
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ContractPaymentsExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "contracts", "contract_payments", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-tahsilatlar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class ExportWarningNoticesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        exporter = BaseExporter(
            user_id=request.user.id,
            app="contracts",
            model_name="WarningNotice",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtarlar.xlsx",
            export_url="/contracts/warning_notices_excel",
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarningNoticesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "contracts", "warning_notices", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtarlar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))