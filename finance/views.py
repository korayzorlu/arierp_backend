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
from .utils import vendor_filter_for_serializers, is_valid_finmaks_transaction_data
from common.models import ImportProcess,ExportProcess,ExchangeRate
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import normalize,safe_decimal,catch_name_from_finmaks_transaction
from purchasing.models import PurchasePayment
from leasing.models import BankActivity

import json
from django.utils.timezone import localtime

# Create your views here.

class AddBankActivityView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        finmaks_transaction = FinmaksTransaction.objects.select_related().filter(transaction_id = data['transaction_id']).first()

        name = catch_name_from_finmaks_transaction(finmaks_transaction)
        if finmaks_transaction.sender_account_name == "None" and not name:
            return JsonResponse({'message': 'İsim algılanamadı! Lütfen gönderen ismini güncelleyiniz.','status':'warning'}, status=400)
        elif finmaks_transaction.sender_account_name == "" and not name:
            return JsonResponse({'message': 'İsim algılanamadı! Lütfen gönderen ismini güncelleyiniz.','status':'warning'}, status=400)

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
            process_date_date = localtime(finmaks_transaction.transaction_date).date(),
            #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
            amount = finmaks_transaction.amount,
            currency = finmaks_transaction.bank_account.currency,
            name = finmaks_transaction.sender_account_name,
            description = finmaks_transaction.explanation_field,
            tc_vkn_no = finmaks_transaction.sender_vkn if finmaks_transaction.sender_vkn and finmaks_transaction.sender_vkn != "None" else None,
        )

        return JsonResponse({'message': 'Başarıyla Gönderildi!','status':'success'}, status=200)

class UpdateFinmaksTransactionNameView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = FinmaksTransaction.objects.select_related().filter(uuid = data['id']).first()
        print(data)
        if obj and data.get('name') and data.get('name') != '':
            obj.sender_account_name = data['name']
            obj.save()

        return JsonResponse({'message': 'Başarıyla Kaydedildi!','status':'success'}, status=200)


class AddFinmaksTransactionView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_finmaks_transaction_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        bank_account = FinmaksBankAccount.objects.filter(uuid = data.get('bank_account')).first()

        print(data.get('transaction_date'))
        print(datetime.strptime(data.get('transaction_date'), '%Y-%m-%d %H:%M'))
        # return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

        obj = FinmaksTransaction.objects.create(
            company = company,
            bank_account = bank_account,
            transaction_id = f"T{get_random_string(length=6, allowed_chars='0123456789')}",
            transaction_date = datetime.strptime(data.get('transaction_date'), '%Y-%m-%d %H:%M') if data.get('transaction_date') else None,
            explanation_field = data.get('description'),
            # description = data.get('description'),
            amount = Decimal(str(data.get('amount'))),
            sender_vkn = data.get('sender_vkn'),
            # sender_iban = data.get('sender_iban'),
            sender_account_name = data.get('sender_account_name'),
            # receiver_vkn = data.get('receiver_vkn'),
            # receiver_iban = data.get('receiver_iban'),
            # receipt_number = data.get('receipt_number'),
            # value_date = make_aware(data.get('value_date')) if data.get('value_date') else None,
            # transaction_type = data.get('transaction_type'),
            # bank_code = data.get('bank_code'),
            # balance = Decimal(str(data.get('balance'))),
            # firm_id = data.get('firm_id'),
            # firm_name = data.get('firm_name'),
            # firm_merchantId = data.get('firm_merchantId'),
            # firm_externalCode = data.get('firm_externalCode'),
            # firm_externalId = data.get('firm_externalId'),
            # transaction_branch_code = data.get('transaction_branch_code'),
            # transaction_branch_name = data.get('transaction_branch_name'),
            # firm_code = data.get('firm_code'),
            # currency_type = data.get('currency_type'),
            debit = data.get('debit'),
            # branch_code = data.get('branch_code'),
            # transaction_external_id = data.get('transaction_external_id'),
            # external_id_used = data.get('external_id_used'),
            # external_bank_id = data.get('external_bank_id'),
            # reference_no = data.get('reference_no'),
            # finmaks_process_type =data.get('finmaks_process_type'),
            # category_name = data.get('category_name'),
            # integration_field_value = data.get('integration_field_value'),
            # transaction_status = data.get('transaction_status')
        )

        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
 

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
    
class BankAccountBalancesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company_uuid = data.get('params').get('activeCompany').get('id') if data.get('params') and data.get('params').get('activeCompany') else None
        active_company = request.user.user_companies.filter(uuid = active_company_uuid).first()

        try_cari_banks = [
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
            {'bank_name' : 'Yapı Kredi', 'account_no' : '1234567890'},
        ]

        try_balance = FinmaksBankAccount.objects.select_related().prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            Q(currency__code = "TRY")
        ).aggregate(
            total_available_balance=Sum('available_balance'),
        )['total_available_balance'] or Decimal('0.00')

        usd_balance = FinmaksBankAccount.objects.select_related().prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            Q(currency__code = "USD")
        ).aggregate(
            total_available_balance=Sum('available_balance'),
        )['total_available_balance'] or Decimal('0.00')

        eur_balance = FinmaksBankAccount.objects.select_related().prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            Q(currency__code = "EUR")
        ).aggregate(
            total_available_balance=Sum('available_balance'),
        )['total_available_balance'] or Decimal('0.00')

        usd_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="USD",date=localtime().date()).first().forex_buying
        eur_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="EUR",date=localtime().date()).first().forex_buying

        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().prefetch_related().filter(
            Q(company = active_company.company if active_company else None)
        )

        bank_accounts = {
            'yapi_kredi': {
                'try' : [],
                'usd' : [],
                'eur' : [],
            },
            'albaraka': {
                'try' : [],
                'usd' : [],
                'eur' : [],
            },
            'vakifbank': {
                'try' : [],
                'usd' : [],
                'eur' : [],
            },
            'vakif_katilim': {
                'try' : [],
                'usd' : [],
                'eur' : [],
            },
            'akbank': {
                'try' : [],
                'usd' : [],
                'eur' : [],
            },
        }
        for finmaks_bank_account in finmaks_bank_accounts:
            if finmaks_bank_account.bank_code == '0067' and finmaks_bank_account.currency.code == 'TRY':
                bank_accounts['yapi_kredi']['try'].append({'id': finmaks_bank_account.uuid, 'account_no': f"TRY - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0067' and finmaks_bank_account.currency.code == 'USD':
                bank_accounts['yapi_kredi']['usd'].append({'id': finmaks_bank_account.uuid, 'account_no': f"USD - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0067' and finmaks_bank_account.currency.code == 'EUR':
                bank_accounts['yapi_kredi']['eur'].append({'id': finmaks_bank_account.uuid, 'account_no': f"EUR - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            
            elif finmaks_bank_account.bank_code == '0203' and finmaks_bank_account.currency.code == 'TRY':
                bank_accounts['albaraka']['try'].append({'id': finmaks_bank_account.uuid, 'account_no': f"TRY - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0203' and finmaks_bank_account.currency.code == 'USD':
                bank_accounts['albaraka']['usd'].append({'id': finmaks_bank_account.uuid, 'account_no': f"USD - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0203' and finmaks_bank_account.currency.code == 'EUR':
                bank_accounts['albaraka']['eur'].append({'id': finmaks_bank_account.uuid, 'account_no': f"EUR - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            
            elif finmaks_bank_account.bank_code == '0015' and finmaks_bank_account.currency.code == 'TRY':
                bank_accounts['vakifbank']['try'].append({'id': finmaks_bank_account.uuid, 'account_no': f"TRY - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0015' and finmaks_bank_account.currency.code == 'USD':
                bank_accounts['vakifbank']['usd'].append({'id': finmaks_bank_account.uuid, 'account_no': f"USD - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0015' and finmaks_bank_account.currency.code == 'EUR':
                bank_accounts['vakifbank']['eur'].append({'id': finmaks_bank_account.uuid, 'account_no': f"EUR - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            
            elif finmaks_bank_account.bank_code == '0210' and finmaks_bank_account.currency.code == 'TRY':
                bank_accounts['vakif_katilim']['try'].append({'id': finmaks_bank_account.uuid, 'account_no': f"TRY - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0210' and finmaks_bank_account.currency.code == 'USD':
                bank_accounts['vakif_katilim']['usd'].append({'id': finmaks_bank_account.uuid, 'account_no': f"USD - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0210' and finmaks_bank_account.currency.code == 'EUR':
                bank_accounts['vakif_katilim']['eur'].append({'id': finmaks_bank_account.uuid, 'account_no': f"EUR - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})

            elif finmaks_bank_account.bank_code == '0046' and finmaks_bank_account.currency.code == 'TRY':
                bank_accounts['akbank']['try'].append({'id': finmaks_bank_account.uuid, 'account_no': f"TRY - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0046' and finmaks_bank_account.currency.code == 'USD':
                bank_accounts['akbank']['usd'].append({'id': finmaks_bank_account.uuid, 'account_no': f"USD - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
            elif finmaks_bank_account.bank_code == '0046' and finmaks_bank_account.currency.code == 'EUR':
                bank_accounts['akbank']['eur'].append({'id': finmaks_bank_account.uuid, 'account_no': f"EUR - {finmaks_bank_account.account_no}",'balance' : finmaks_bank_account.available_balance})
                
        bank_accounts['yapi_kredi']['try'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0067', currency__code='TRY').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['yapi_kredi']['usd'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0067', currency__code='USD').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['yapi_kredi']['eur'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0067', currency__code='EUR').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })

        bank_accounts['albaraka']['try'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0203', currency__code='TRY').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['albaraka']['usd'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0203', currency__code='USD').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['albaraka']['eur'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0203', currency__code='EUR').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })

        bank_accounts['vakifbank']['try'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0015', currency__code='TRY').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['vakifbank']['usd'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0015', currency__code='USD').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['vakifbank']['eur'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0015', currency__code='EUR').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })

        bank_accounts['vakif_katilim']['try'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0210', currency__code='TRY').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['vakif_katilim']['usd'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0210', currency__code='USD').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['vakif_katilim']['eur'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0210', currency__code='EUR').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })

        bank_accounts['akbank']['try'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0046', currency__code='TRY').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['akbank']['usd'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0046', currency__code='USD').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
        bank_accounts['akbank']['eur'].append({
            'id': '999',
            'account_no':"TOPLAM",
            'balance' : finmaks_bank_accounts.filter(bank_code='0046', currency__code='EUR').aggregate(total_available_balance=Sum('available_balance'))['total_available_balance'] or Decimal('0.00')
        })
            

        # data = {
        #     'active_balances' : [
        #         {'id': 1, 'label':'TRY Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': try_balance},
        #         {'id': 2, 'label':'USD Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': usd_balance},
        #         {'id': 3, 'label':'USD/TRY Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': usd_balance*usd_exchange_rate},
        #         {'id': 4, 'label':'EUR Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': eur_balance},
        #         {'id': 5, 'label':'EUR/TRY Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': eur_balance*eur_exchange_rate},
        #         {'id': 6, 'label':'Toplam TRY Bakiye', 'two_days_ago_amount': Decimal('0.00'), 'yesterday_amount': Decimal('0.00'), 'current_amount': try_balance + (usd_balance*usd_exchange_rate) + (eur_balance*eur_exchange_rate)},
        #     ]
            
        # }

        data = {
            'active_balances' : {
                'try_balance': try_balance,
                'usd_balance': usd_balance,
                'usd_try_balance': usd_balance * usd_exchange_rate,
                'eur_balance': eur_balance,
                'eur_try_balance': eur_balance * eur_exchange_rate,
                'total_try_balance': try_balance + (usd_balance*usd_exchange_rate) + (eur_balance*eur_exchange_rate),
            },
            'bank_accounts' : bank_accounts,
        }

        return JsonResponse({'data':data}, status=200)