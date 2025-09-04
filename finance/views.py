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
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.utils.timezone import make_aware

from utils.mixins import CompanyOwnershipRequiredMixin

from .models import *
from .utils import vendor_filter_for_serializers
from common.models import ImportProcess,ExportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import normalize,safe_decimal
from purchasing.models import PurchasePayment
from leasing.models import BankActivity

import json

# Create your views here.

class AddBankActivityView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        print(data)

        finmaks_transaction = FinmaksTransaction.objects.select_related().filter(transaction_id = data['transaction_id']).first()

        BankActivity.objects.create(
            company = self.request.user.user_companies.filter(is_active=True).first().company,
            finmaks_transaction = finmaks_transaction,
            bank_code = finmaks_transaction.bank_code,
            bank_branch_code = finmaks_transaction.branch_code,
            bank_account_no = finmaks_transaction.bank_account.account_no,
            cross_bank_code = finmaks_transaction.bank_code,
            cross_bank_branch_code = finmaks_transaction.transaction_branch_code,
            cross_bank_account_no = finmaks_transaction.sender_iban,
            process_code = finmaks_transaction.transaction_id,
            credit_or_debit = "C" if finmaks_transaction.debit == "+" else "D",
            kontrat_no = finmaks_transaction.receipt_number,
            process_date_date = finmaks_transaction.transaction_date.date(),
            #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
            amount = finmaks_transaction.amount,
            currency = finmaks_transaction.bank_account.currency,
            name = finmaks_transaction.sender_account_name,
            description = finmaks_transaction.explanation_field,
            tc_vkn_no = finmaks_transaction.sender_vkn,
        )

        return JsonResponse({'message': 'Başarıyla Gönderildi!','status':'success'}, status=200)
    
class FinanceSummaryView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company_uuid = data.get('params').get('activeCompany').get('id')
        active_company = request.user.user_companies.filter(uuid = active_company_uuid).first()
        
        vendors_try = PurchasePayment.objects.select_related("lease__contract__vendor").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params'))  &
            Q(lease__currency__code = "TRY")
        ).aggregate(
            total_total_contract_amount=Sum('total_contract_amount'),
            total_before_total_payment=Sum('before_total_payment'),
            total_after_total_payment=Sum('after_total_payment'),
            total_managing_expense=Sum('managing_expense'),
            total_lease_payment_amount=Sum('lease_payment_amount'),
            total_total_vendor_payment=Sum('total_vendor_payment')
        )

        vendors_usd = PurchasePayment.objects.select_related("lease__contract__vendor").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params'))  &
            Q(lease__currency__code = "USD")
        ).aggregate(
            total_total_contract_amount=Sum('total_contract_amount'),
            total_before_total_payment=Sum('before_total_payment'),
            total_after_total_payment=Sum('after_total_payment'),
            total_managing_expense=Sum('managing_expense'),
            total_lease_payment_amount=Sum('lease_payment_amount'),
            total_total_vendor_payment=Sum('total_vendor_payment')
        )

        vendors_eur = PurchasePayment.objects.select_related("lease__contract__vendor").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params'))  &
            Q(lease__currency__code = "EUR")
        ).aggregate(
            total_total_contract_amount=Sum('total_contract_amount'),
            total_before_total_payment=Sum('before_total_payment'),
            total_after_total_payment=Sum('after_total_payment'),
            total_managing_expense=Sum('managing_expense'),
            total_lease_payment_amount=Sum('lease_payment_amount'),
            total_total_vendor_payment=Sum('total_vendor_payment')
        )


        manager_summary = [
            {   
                'id': 1,
                'title': 'Toplam Sözleşme Bedeli',
                'amount_try': float(vendors_try['total_total_contract_amount']) if vendors_try['total_total_contract_amount'] else 0.00,
                'amount_usd': float(vendors_usd['total_total_contract_amount']) if vendors_usd['total_total_contract_amount'] else 0.00,
                'amount_eur': float(vendors_eur['total_total_contract_amount']) if vendors_eur['total_total_contract_amount'] else 0.00
            },
            {   
                'id': 2,
                'title': 'Ödeme Toplam Öncesi',
                'amount_try': float(vendors_try['total_before_total_payment']) if vendors_try['total_before_total_payment'] else 0.00,
                'amount_usd': float(vendors_usd['total_before_total_payment']) if vendors_usd['total_before_total_payment'] else 0.00,
                'amount_eur': float(vendors_eur['total_before_total_payment']) if vendors_eur['total_before_total_payment'] else 0.00
            },
            {   
                'id': 3,
                'title': 'Toplam Ödeme Sonrası',
                'amount_try': float(vendors_try['total_after_total_payment']) if vendors_try['total_after_total_payment'] else 0.00,
                'amount_usd': float(vendors_usd['total_after_total_payment']) if vendors_usd['total_after_total_payment'] else 0.00,
                'amount_eur': float(vendors_eur['total_after_total_payment']) if vendors_eur['total_after_total_payment'] else 0.00
            },
            {   
                'id': 4,
                'title': 'Toplam Yönetim Gideri',
                'amount_try': float(vendors_try['total_managing_expense']) if vendors_try['total_managing_expense'] else 0.00,
                'amount_usd': float(vendors_usd['total_managing_expense']) if vendors_usd['total_managing_expense'] else 0.00,
                'amount_eur': float(vendors_eur['total_managing_expense']) if vendors_eur['total_managing_expense'] else 0.00
            },
            {   
                'id': 5,
                'title': 'Toplam Kira Tahsilat Tutarı',
                'amount_try': float(vendors_try['total_lease_payment_amount']) if vendors_try['total_lease_payment_amount'] else 0.00,
                'amount_usd': float(vendors_usd['total_lease_payment_amount']) if vendors_usd['total_lease_payment_amount'] else 0.00,
                'amount_eur': float(vendors_eur['total_lease_payment_amount']) if vendors_eur['total_lease_payment_amount'] else 0.00
            },
            {   
                'id': 6,
                'title': 'Toplam Satıcı Ödemeleri Tutarı',
                'amount_try': float(vendors_try['total_total_vendor_payment']) if vendors_try['total_total_vendor_payment'] else 0.00,
                'amount_usd': float(vendors_usd['total_total_vendor_payment']) if vendors_usd['total_total_vendor_payment'] else 0.00,
                'amount_eur': float(vendors_eur['total_total_vendor_payment']) if vendors_eur['total_total_vendor_payment'] else 0.00
            },
            {   
                'id': 7,
                'title': 'Toplam Temerrüt Tutarı',
                'amount_try': float(vendors_try['total_before_total_payment'] - vendors_try['total_lease_payment_amount']) if vendors_try['total_total_vendor_payment'] else 0.00,
                'amount_usd': float(vendors_usd['total_before_total_payment'] - vendors_usd['total_lease_payment_amount']) if vendors_usd['total_total_vendor_payment'] else 0.00,
                'amount_eur': float(vendors_eur['total_before_total_payment'] - vendors_eur['total_lease_payment_amount']) if vendors_eur['total_total_vendor_payment'] else 0.00
            },
        ]

        return JsonResponse({'data':manager_summary}, status=200)