from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse

from utils.mixins import CompanyOwnershipRequiredMixin

import json
from decimal import Decimal

from accounting.models import *
from accounting.utils import is_valid_account_data, is_valid_invoice_data

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
   