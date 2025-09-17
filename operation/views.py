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


import json

# Create your views here.

class AddPartnerAdvanceActivityView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        partner = Partner.objects.select_related().filter(uuid = data['uuid']).first()

        PartnerAdvanceActivity.objects.create(
            company = self.request.user.user_companies.filter(is_active=True).first().company,
            partner = partner,
            # bank_code = finmaks_transaction.bank_code,
            # bank_branch_code = finmaks_transaction.branch_code,
            # bank_account_no = finmaks_transaction.bank_account.account_no,
            # cross_bank_code = finmaks_transaction.bank_code,
            # cross_bank_branch_code = finmaks_transaction.transaction_branch_code,
            # cross_bank_account_no = finmaks_transaction.sender_iban,
            # process_code = finmaks_transaction.transaction_id,
            # credit_or_debit = "C" if finmaks_transaction.debit == "+" else "D",
            # kontrat_no = finmaks_transaction.receipt_number,
            # process_date_date = finmaks_transaction.transaction_date.date(),
            #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
            # amount = finmaks_transaction.amount,
            # currency = finmaks_transaction.bank_account.currency,
            name = partner.name,
            # description = finmaks_transaction.explanation_field,
            tc_vkn_no = partner.tc_vkn_no,
        )

        return JsonResponse({'message': 'Başarıyla Gönderildi!','status':'success'}, status=200)