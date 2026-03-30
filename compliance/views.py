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

from utils.mixins import CompanyOwnershipRequiredMixin

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date,datetime

from .models import *
from .utils.black_list_person_utils import is_valid_black_list_person_data
from .utils.third_person_utils import send_email_for_third_person_cleared,send_email_for_third_person_to_cleared
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert
from common.models import ExportProcess
from common.utils.export_utils import BaseExporter

# Create your views here.

class UpdateThirdPersonStatusView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if request.user.authorization.department != 'kredi_tahsiss':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        obj = ThirdPerson.objects.select_related().filter(uuid = data.get('uuid')).first()

        if ThirdPersonDocument.objects.filter(third_person = obj).exists() and data.get('status') == 'cleared':
            obj.status = 'cleared'
        elif obj.status == 'need_document':
            obj.status = data.get('status')
        else:
            obj.status = data.get('status') if data.get('status') == 'flagged' else 'need_document'

        if data.get('status') == 'cleared':
            send_email_for_third_person_to_cleared(obj.name,obj.tc_vkn_no)
            obj.is_email_sent = True
        obj.save()

        bank_activities = obj.bank_activities.select_related().all()
        new_date = date.today()
        for bank_activity in bank_activities:
            bank_activity.is_reliable_person = True if data.get('status') == 'cleared' else False
            bank_activity.third_person_status = data.get('status')
            if data.get('status') == 'cleared':
                current_date=obj.created_date
                updated_date=datetime.combine(new_date,current_date.time())
                obj.created_date=updated_date
            bank_activity.save()

        return JsonResponse({'message': 'Durum değiştirildi!','status':'success'}, status=200)
    
class UpdateThirdPersonIsEmailSentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        
        if request.user.authorization.department != 'operasyon':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        obj = ThirdPerson.objects.select_related().filter(uuid = data.get('id')).first()
        obj.is_email_sent = data.get('is_email_sent')
        obj.save()

        return JsonResponse({'message': 'Durum değiştirildi!','status':'success'}, status=200)
    
class UpdateThirdPersonIsCustomerSentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if request.user.authorization.department != 'finans' and request.user.authorization.department != 'operasyon' and request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)
        
        obj = ThirdPerson.objects.select_related().filter(uuid = data.get('id')).first()
        obj.is_customer_sent = True
        obj.save()

        return JsonResponse({'message': 'Durum değiştirildi!','status':'success'}, status=200)
    
class AddBlackListPersonView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        if request.user.authorization.department != 'kredi_tahsis':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)
        
        valid, response = is_valid_black_list_person_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        obj = BlackListPerson.objects.create(
            company = company,
            name = data.get('name'),
            tc_vkn_passport_no = data.get('tc_vkn_passport_no'),
            other_names = data.get('other_names'),
            nationality = data.get('nationality'),
            birthday = data.get('birthday'),
            organization = data.get('organization'),
            date_number = data.get('date_number'),
        )

        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
    
class ImportThirdPersonDocumentsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({'message': 'Yüklenecek dosya bulunamadı!','status':'error'}, status=400)
        
        if file.size > settings.MAX_UPLOAD_SIZE:
            return JsonResponse({'message': 'Dosya boyutu fazla! Max 1MB yükleyebilirsiniz.','status':'error'}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Yetki hatası!.','status':'error'}, status=401)
        
        if request.user.authorization.department != 'operasyon':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)

        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        obj = ThirdPerson.objects.filter(uuid = data.get('uuid'), company = active_company.company).first()

        if not obj:
            return JsonResponse({'message': 'Bir hata oluştu!','status':'error'}, status=400)
        
        ThirdPersonDocument.objects.create(
            company = active_company.company,
            third_person = obj,
            label = file.name,
            file = file,
        )

        obj.status = 'cleared'
        obj.save()

        obj.bank_activities.update(
            is_reliable_person = True,
            third_person_status = 'cleared',
            created_date = datetime.now()
        )

        send_email_for_third_person_cleared(obj.name,obj.tc_vkn_no)
        
        return JsonResponse({'message': 'Dosya başarıyla yüklendi!','status':'success'}, status=200)

class VPosThirdPersonsTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "sanal-pos-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportVPosThirdPersonsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="compliance", model_name="ThirdPerson", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Veriler yükleniyor...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)
    
class ExportThirdPersonsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="compliance",
            model_name="ThirdPerson",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-ucuncu-kisiler.xlsx",
            export_url="/compliance/third_persons_excel",
            params={"status":data.get('status')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class ThirdPersonsExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "compliance", "third_persons", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-ucuncu-kisiler.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))
 