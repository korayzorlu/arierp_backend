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


from utils.mixins import CompanyOwnershipRequiredMixin

from .models import *
from .utils import vendor_filter_for_serializers
from common.models import ImportProcess,ExportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from purchasing.models import PurchasePayment

import json

# Create your views here.

class AddBankActivityView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        print(data)

        return JsonResponse({'message': 'Başarıyla Gönderildi!','status':'success'}, status=200)
    
class FinanceSummaryView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company_uuid = data.get('params').get('activeCompany').get('id')
        active_company = request.user.user_companies.filter(uuid = active_company_uuid).first()

        vendors = PurchasePayment.objects.select_related("lease__contract__vendor").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) 
        ).aggregate(
            total_before_total_payment=Sum('before_total_payment'),
            total_after_total_payment=Sum('after_total_payment'),
            total_managing_expense=Sum('managing_expense')
        )


        manager_summary = [
            {   
                'id': 1,
                'title': 'Ödeme Toplam Öncesi',
                'amount': float(vendors['total_before_total_payment']) if vendors['total_before_total_payment'] else 0.00
            },
            {   
                'id': 2,
                'title': 'Toplam Ödeme Sonrası',
                'amount': float(vendors['total_after_total_payment']) if vendors['total_after_total_payment'] else 0.00
            },
            {   
                'id': 3,
                'title': 'Yönetim Gideri',
                'amount': float(vendors['total_managing_expense']) if vendors['total_managing_expense'] else 0.00
            },
        ]

        return JsonResponse({'data':manager_summary}, status=200)