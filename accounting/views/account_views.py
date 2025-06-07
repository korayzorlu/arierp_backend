from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse

from utils.mixins import CompanyOwnershipRequiredMixin

import json
from decimal import Decimal

from accounting.models import *
from accounting.utils import is_valid_account_data, is_valid_invoice_data

class AddAccountView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_account_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        if data.get('partner'):
            partner = Partner.objects.filter(uuid = data.get('partner').get('uuid')).first()
        else:
            partner = None
            
        currency = Currency.objects.filter(code = data.get('currency') if data.get('currency') else 0).first()

        type = AccountType.objects.filter(code=data.get('type')).first()

        if data.get('type') == "receivable" or data.get('type') == "payable" or data.get('type') == "shareholder":
            if Account.objects.filter(partner=partner,currency=currency).exists():
                return JsonResponse({'message': 'An account with this currency already exists for this partner.','status':'error'}, status=400)
        else:
            if Account.objects.filter(type=type,currency=currency).exists():
                return JsonResponse({'message': 'An account with this currency already exists for this partner.','status':'error'}, status=400)

        account = Account.objects.create(
            company = company,
            type = type,
            partner = partner,
            currency = currency,
        )
        account.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)

class UpdateAccountView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Account
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_account_data(data)
        if not valid:
            return response

        partner = Partner.objects.filter(uuid = data.get('partner').get('uuid')).first()
        currency = Currency.objects.filter(code = data.get('currency') if data.get('currency') else 0).first()

        obj = Account.objects.filter(uuid = data.get('uuid')).first()

        if obj.account_transactions.all().exists():
            if partner != obj.partner or currency != obj.currency:
                return JsonResponse({'message': 'Transactions are linked to this account, partner or currency cannot be changed.','status':'error'}, status=400)
        
        obj.type = AccountType.objects.filter(code=data.get('type')).first()
        obj.partner = partner
        obj.currency = currency
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteAccountView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Account
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if isinstance(data.get("uuid"),str):
            obj = Account.objects.filter(uuid = data.get('uuid')).first()

            if obj.account_transactions.all().exists():
                return JsonResponse({'message': 'This account has linked transactions and cannot be deleted.','status':'error'}, status=400)
            
            obj.delete()
        elif isinstance(data.get("uuids"),list):
            for uuid in data.get("uuids"):
                obj = Account.objects.filter(uuid = uuid).first()

                if obj.account_transactions.all().exists():
                    return JsonResponse({'message': 'An account has linked transactions and cannot be deleted.','status':'error'}, status=400)
            
                obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)


class DeletePartnersView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            partner = Partner.objects.filter(uuid = uuid).first()
            partner.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
