from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utils.mixins import CompanyOwnershipRequiredMixin

from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.models import ExportProcess

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

# Create your views here.

class ExportRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="RiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar-sms.xlsx",
            export_url="/risk/risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class RiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))


class ExportRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="RiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar.xlsx",
            export_url="/risk/risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class RiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))




class ExportToWarnedRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToWarnedRiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler-sms.xlsx",
            export_url="/risk/to_warned_risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToWarnedRiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))

class ExportToWarnedRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToWarnedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler.xlsx",
            export_url="/risk/to_warned_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToWarnedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))



class ExportWarnedRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="WarnedRiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler-sms.xlsx",
            export_url="/risk/warned_risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarnedRiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))


class ExportWarnedRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="WarnedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx",
            export_url="/risk/warned_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarnedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))




class ExportToTerminatedRiskPartnersForSMSView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToTerminatedRiskPartnerForSMS",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler-sms.xlsx",
            export_url="/risk/to_terminated_risk_partners_excel_for_sms",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToTerminatedRiskPartnersExcelForSMSView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler-sms.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))


class ExportToTerminatedRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="ToTerminatedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx",
            export_url="/risk/to_terminated_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToTerminatedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "to_terminated_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))




class ExportAmountDebitTransactionsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        exporter = BaseExporter(
            user_id=request.user.id,
            app="risk",
            model_name="AmountDebitTransaction",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-bakiye-temerrut-raporu.xlsx",
            export_url="/risk/amount_debit_transactions_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class AmountDebitTransactionsExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "risk", "amount_debit_transaction", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-bakiye-temerrut-raporu.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    