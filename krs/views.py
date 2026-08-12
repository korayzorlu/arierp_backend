from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponse,JsonResponse,FileResponse
from django.utils import timezone

from leasing.models import Lease
from common.utils.websocket_utils import send_alert
from .utils.report_utils import create_krs_report
from .models import KrsReportDocument

import os
import json
from datetime import datetime, timedelta

class CreateKrsReportView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company = request.user.user_companies.filter(uuid = data.get('company_uuid')).first()

        report_base_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        if report_base_date.weekday() == 0: # Pazartesi
            days_back = 3
        elif report_base_date.weekday() == 6: # Pazar
            days_back = 2
        else:
            days_back = 1
        report_date = report_base_date - timezone.timedelta(days=days_back)

        create_krs_report(str(active_company.company.uuid),report_date, report_base_date)

        return JsonResponse({'message': 'Rapor hazırlanıyor...','status':'success'}, status=200)
    
class GetKrsReportDocumentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company = request.user.user_companies.filter(uuid = data.get('company_uuid')).first()

        obj = KrsReportDocument.objects.filter(
            company = active_company.company if active_company else None
        ).order_by("-created_date").first()

        if not obj or not os.path.exists(obj.file.path):
            return JsonResponse({'message': 'Dosya bulunamadı!','status':'error'}, status=404)

        return FileResponse(open(obj.file.path, 'rb'), as_attachment=True, filename=obj.label or os.path.basename(obj.file.name))