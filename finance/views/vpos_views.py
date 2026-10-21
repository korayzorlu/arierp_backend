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
from django.utils.timezone import make_aware, is_aware
from dateutil import parser as dateutil_parser

from utils.mixins import CompanyOwnershipRequiredMixin

from finance.models import *
from finance.utils.vpos_utils import is_valid_vpos_transaction_data, add_vpos_transation
from common.models import ImportProcess,ExportProcess,ExchangeRate
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_datetime,safe_decimal
from purchasing.models import PurchasePayment
from leasing.models import BankActivity

import json
import os
from django.utils.timezone import localtime

# Create your views here.

class AddVPosTransactionView(View):
    def post(self, request, *args, **kwargs):
        if request.body:
            data = json.loads(request.body)
        else:
            data = request.POST.dict() or request.GET.dict()
        
        valid, response = is_valid_vpos_transaction_data(data)
        if not valid:
            return response
        
        add_vpos_transation(data)

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
