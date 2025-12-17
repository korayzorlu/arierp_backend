from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.conf import settings

from utils.mixins import CompanyOwnershipRequiredMixin

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

class ExportTrialBalancesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if ExportProcess.objects.filter(user=request.user,model_name="TrialBalance",status__in=["pending","in_progress"]).exists():
            return JsonResponse({'message':'Bu tablo için başka bir dışarı aktarma işlemi devam ediyor! Lütfen bekleyin.','status':'error'}, status=400)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="accounting",
            model_name="TrialBalance",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-mizan.xlsx",
            export_url="/accounting/trial_balances_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class TrialBalancesExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "accounting", "trial_balances", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-mizan.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))