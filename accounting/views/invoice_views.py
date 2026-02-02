from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.conf import settings

from utils.mixins import CompanyOwnershipRequiredMixin

import json
from decimal import Decimal
import os
import json
from decimal import Decimal
from datetime import datetime

from accounting.models import *
from accounting.utils.common_utils import is_valid_account_data, is_valid_invoice_data
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_amount
from common.models import ExportProcess


class AddInvoiceView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_invoice_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        partner = Partner.objects.filter(uuid = data.get('partner').get('uuid')).first()
        currency = Currency.objects.filter(code = data.get('currency') if data.get('currency') else 0).first()

        invoice = Invoice.objects.create(
            company = company,
            type = data.get('type'),
            partner = partner,
            currency = currency,
            amount = Decimal(str(data.get('amount'))),
            invoice_no = data.get('invoice_no'),
        )
        invoice.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)

class UpdateInvoiceView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Invoice
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_invoice_data(data)
        if not valid:
            return response

        partner = Partner.objects.filter(uuid = data.get('partner').get('uuid')).first()
        currency = Currency.objects.filter(code = data.get('currency') if data.get('currency') else 0).first()

        obj = Invoice.objects.filter(uuid = data.get('uuid')).first()
        obj.type = data.get('type')
        obj.partner = partner
        obj.currency = currency
        obj.amount = Decimal(str(data.get('amount')))
        obj.invoice_no = data.get('invoice_no')
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
 
class DeleteInvoiceView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Invoice
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if isinstance(data.get("uuid"),str):
            obj = Invoice.objects.filter(uuid = data.get('uuid')).first()
            obj.delete()
        elif isinstance(data.get("uuids"),list):
            for uuid in data.get("uuids"):
                obj = Invoice.objects.filter(uuid = uuid).first()
                obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)



class ExportInvoicesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if ExportProcess.objects.filter(user=request.user,model_name="Invoice",status__in=["pending","in_progress"]).exists():
            return JsonResponse({'message':'Bu tablo için başka bir dışarı aktarma işlemi devam ediyor! Lütfen bekleyin.','status':'error'}, status=400)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="accounting",
            model_name="Invoice",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-faturalar.xlsx",
            export_url="/accounting/invoices_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class InvoicesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "accounting", "invoices", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-faturalar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))