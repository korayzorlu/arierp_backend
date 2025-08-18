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

from leasing.models import *
from leasing.utils import is_valid_lease_data,vendor_filter_for_serializers,vendor_filter_for_views
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_amount
from partners.models import Partner
from contracts.models import Contract
from companies.models import UserCompany
from common.models import ExportProcess
from projects.models import Project

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

# Create your views here.

class AddLeaseView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_lease_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        contract = Contract.objects.filter(uuid = data.get('contract')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Lease.objects.create(
            company = company,
            code = data.get('code'),
            contract = contract,
            type = data.get('kof'),
            vat = Decimal(str(data.get('quotation'))),
            activation_date = data.get('activation_date'),
            lease_status = data.get('lease_status'),
            currency = currency,
            musteri_baz_maliyet = Decimal(str(data.get('musteri_baz_maliyet'))),    
            vade =int( data.get('vade')),
            leasing_rate = Decimal(str(data.get('leasing_rate'))),
            irr = Decimal(str(data.get('irr'))),
            project_no = data.get('project_no'),
            status = status,
            leasing_type = data.get('leasing_type'),
            application_no = data.get('application_no'),
            is_last_project = data.get('is_last_project'),
            current_request = data.get('current_request'),
            finansman_kurum = data.get('finansman_kurum'),
            is_tufe = data.get('is_tufe'),
            is_musterek = data.get('is_musterek'),
            bbsn = data.get('bbsn'),
        )
        obj.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateLeaseView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_lease_data(data)
        if not valid:
            return response

        contract = Contract.objects.filter(uuid = data.get('contract')).first()
        currency = Currency.objects.filter(uuid = data.get('currency')).first()
        status = Status.objects.filter(uuid = data.get('status')).first()

        obj = Lease.objects.filter(uuid = data.get('uuid')).first()
        obj.code = data.get('code'),
        obj.contract = contract,
        obj.type = data.get('kof'),
        obj.vat = Decimal(str(data.get('quotation'))),
        obj.activation_date = data.get('activation_date'),
        obj.lease_status = data.get('lease_status'),
        obj.currency = currency,
        obj.musteri_baz_maliyet = Decimal(str(data.get('musteri_baz_maliyet'))),    
        obj.vade =int( data.get('vade')),
        obj.leasing_rate = Decimal(str(data.get('leasing_rate'))),
        obj.irr = Decimal(str(data.get('irr'))),
        obj.project_no = data.get('project_no'),
        obj.status = status,
        obj.leasing_type = data.get('leasing_type'),
        obj.application_no = data.get('application_no'),
        obj.is_last_project = data.get('is_last_project'),
        obj.current_request = data.get('current_request'),
        obj.finansman_kurum = data.get('finansman_kurum'),
        obj.is_tufe = data.get('is_tufe'),
        obj.is_musterek = data.get('is_musterek'),
        obj.bbsn = data.get('bbsn'),
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteLeaseView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Lease.objects.filter(uuid = data.get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Lease.objects.filter(uuid = uuid).first()
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        objs = Lease.objects.filter()
        for obj in objs:
            obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class LeasesTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "leases-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportLeasesView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="leasing", model_name="Lease", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)



class UpdateLeaseflexAutomationLeasesView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            obj = Lease.objects.filter(uuid = uuid).first()
            obj.leaseflex_automation = data.get('select') or False
            obj.save()

        return JsonResponse({'message': 'Seçim değiştirildi!','status':'success'}, status=200)
    
class UpdateLeaseProcessedAmountView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Lease

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Lease.objects.filter(uuid = data.get('uuid')).first()

        
        obj.processed_amount = Decimal(str(data.get('amount')).replace(",","."))
        obj.save()

        return JsonResponse({'message': 'Tutar değiştirildi!','status':'success'}, status=200)
    
class OverdueInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        lease_code = data.get('lease_code')

        # active_company_uuid = data.get('active_company')
        # active_company = UserCompany.objects.select_related("company").filter(uuid = active_company_uuid).first()
        
        objs = Lease.objects.select_related().filter(code = str(lease_code))
        
        if not objs:
            return JsonResponse({'overdue':[]}, status=200)
        
        overdue_data = [
            {   
                'id': obj.uuid,
                'lease': obj.code if obj else "",
                'overdue_0_30': obj.overdue_0_30 if obj else Decimal("0.00"),
                'overdue_31_60': obj.overdue_31_60 if obj else Decimal("0.00"),
                'overdue_61_90': obj.overdue_61_90 if obj else Decimal("0.00"),
                'overdue_91_120': obj.overdue_91_120 if obj else Decimal("0.00"),
                'overdue_121_150': obj.overdue_121_150 if obj else Decimal("0.00"),
                'overdue_151_180': obj.overdue_151_180 if obj else Decimal("0.00"),
                'overdue_181_gte': obj.overdue_181_gte if obj else Decimal("0.00"),
            }
            for obj in objs
        ]

        return JsonResponse({'overdue':overdue_data}, status=200)
    
class ExportTodayPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        exporter = BaseExporter(
            user_id=request.user.id,
            app="leasing",
            model_name="TodayPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-bugün-ödemesi-olanlar.xlsx",
            export_url="/leasing/today_partners_excel",
            params={"project": data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class TodayPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "today_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-bugün-ödemesi-olanlar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class ExportTomorrowPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        exporter = BaseExporter(
            user_id=request.user.id,
            app="leasing",
            model_name="TomorrowPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-yarın-ödemesi-olanlar.xlsx",
            export_url="/leasing/tomorrow_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class TomorrowPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "tomorrow_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-yarın-ödemesi-olanlar.xlsx")
      
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
            app="leasing",
            model_name="RiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar.xlsx",
            export_url="/leasing/risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class RiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class ExportKDVRiskPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="leasing",
            model_name="KDVRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-kdv-farkı-uygulananlar.xlsx",
            export_url="/leasing/kdv_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class KDVRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-kdv-farkı-uygulananlar.xlsx")
      
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
            app="leasing",
            model_name="ToWarnedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler.xlsx",
            export_url="/leasing/to_warned_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToWarnedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "to_warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler.xlsx")
      
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
            app="leasing",
            model_name="WarnedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx",
            export_url="/leasing/warned_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class WarnedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "warned_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx")
      
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
            app="leasing",
            model_name="ToTerminatedRiskPartner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx",
            export_url="/leasing/to_terminated_risk_partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ToTerminatedRiskPartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "to_terminated_risk_partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class ExportDeliveryConfirmsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="leasing",
            model_name="DeliveryConfirm",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-teslim-onay.xlsx",
            export_url="/leasing/delivery_confirms_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class DeliveryConfirmsExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "leasing", "delivery_confirms", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-teslim-onay.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
    
class ManagerSummaryView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company_uuid = data.get('params').get('activeCompany').get('id')
        active_company = request.user.user_companies.filter(uuid = active_company_uuid).first()
        
        overdue_leases = Lease.objects.select_related("contract","contract__partner").prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=30) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff = False) &
            Q(is_credit=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            )
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
        ).filter(warning_notice_count__gt=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_terminated_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        manager_summary = [
            {   
                'id': 1,
                'title': 'Vadesi Geçmişler',
                'amount': float(overdue_leases['total_overdue_amount']) if overdue_leases['total_overdue_amount'] else 0.00,
                'quantity': overdue_leases['count_overdue_leases'] or 0,
                'partner': overdue_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 2,
                'title': 'İhtar Çekilecekler',
                'amount': float(to_warned_leases['total_overdue_amount']) if to_warned_leases['total_overdue_amount'] else 0.00,
                'quantity': to_warned_leases['count_overdue_leases'] or 0,
                'partner': to_warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 3,
                'title': 'İhtar Çekilenler',
                'amount': float(warned_leases['total_overdue_amount']) if warned_leases['total_overdue_amount'] else 0.00,
                'quantity': warned_leases['count_overdue_leases'] or 0,
                'partner': warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 4,
                'title': 'Fesih Edilecekler',
                'amount': float(to_terminated_leases['total_overdue_amount']) if to_terminated_leases['total_overdue_amount'] else 0.00,
                'quantity': to_terminated_leases['count_overdue_leases'] or 0,
                'partner': to_terminated_leases['count_distinct_partners'] or 0
            }
        ]

        return JsonResponse({'data':manager_summary}, status=200)