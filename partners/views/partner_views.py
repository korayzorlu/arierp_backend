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
from django.core.mail import EmailMessage, send_mail

from utils.mixins import CompanyOwnershipRequiredMixin,ActivityLogMixin

from partners.models import *
from partners.tasks import importPartners
from partners.utils.common_utils import is_valid_partner_data, get_partner_types
from partners.utils.partner_utils import *
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.models import ExportProcess

import os
import json
import pandas as pd
from datetime import datetime

# Create your views here.

class AddPartnerView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        valid, response = is_valid_partner_data(data)
        if not valid:
            return response
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)
        
        country = Country.objects.filter(iso2 = data.get('country') if data.get('country') else 0).first()
        city = City.objects.filter(country__iso2 = data.get('country') if data.get('country') else 0,id = int(data.get('city').get("id")) if data.get('city') else 0).first()
        billing_country = Country.objects.filter(iso2 = data.get('billingCountry') if data.get('billingCountry') else 0).first()
        billing_city = City.objects.filter(country__iso2 = data.get('billingCountry') if data.get('billingCountry') else 0,id = int(data.get('billingCity').get("id")) if data.get('billingCity') else 0).first()

        phone_country = Country.objects.filter(iso2 = data.get('phoneCountry') if data.get('phoneCountry') else 0).first()

        partner = Partner.objects.create(
            types = get_partner_types(data),
            company = company,
            name = data.get('name'),
            formal_name = data.get('formalName'),
            vat_office = data.get('vatOffice'),
            vat_no = data.get('vatNo'),
            country = country,
            city = city,
            address = data.get('address'),
            address2 = data.get('address2'),
            is_billing_same = data.get('isBillingSame') or False,
            billing_country = country if data.get('isBillingSame') else billing_country,
            billing_city = city if data.get('isBillingSame') else billing_city,
            billing_address = data.get('address') if data.get('isBillingSame') else data.get('billingAddress'),
            billing_address2 = data.get('address2') if data.get('isBillingSame') else data.get('billingAddress2'),
            phone_country = phone_country if data.get('phoneNumber') else None,
            phone_number = data.get('phoneNumber') if phone_country else None,
            email = data.get('email'),
            web = data.get('web'),
            about = data.get('about')
        )
        partner.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdatePartnerView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        valid, response = is_valid_partner_data(data)
        if not valid:
            return response
        
        # country = Country.objects.filter(iso2 = data.get('country') if data.get('country') else 0).first()
        # city = City.objects.filter(country__iso2 = data.get('country') if data.get('country') else 0,id = int(data.get('city').get("id")) if data.get('city') else 0).first()
        # billing_country = Country.objects.filter(iso2 = data.get('billingCountry') if data.get('billingCountry') else 0).first()
        # billing_city = City.objects.filter(country__iso2 = data.get('billingCountry') if data.get('billingCountry') else 0,id = int(data.get('billingCity').get("id")) if data.get('billingCity') else 0).first()

        # phone_country = Country.objects.filter(iso2 = data.get('phoneCountry') if data.get('phoneCountry') else 0).first()

        obj = Partner.objects.filter(uuid = data.get('uuid')).first()

        if not obj.is_reliable_person:
            send_warning_email_for_ignored_partners({
                'name': obj.name,
                'tc_vkn_no': obj.tc_vkn_no,
                'crm_code': obj.crm_code,
                'request_user_full_name': request.user.get_full_name(),
                'request_user_email': request.user.email
            })
            # today = datetime.today().date().strftime("%d.%m.%Y")
                
            # def send_outlook_email(subject, message, from_email, recipient_list, attachments=None):
            #     email = EmailMessage(
            #         subject,
            #         message,
            #         from_email,
            #         recipient_list,
            #     )
            #     if attachments:
            #         for attachment in attachments:
            #             email.attach(attachment['name'], attachment['content'], attachment['mimetype'])
            #     email.send(fail_silently=False)
            #     #send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    
            # subject = 'YASAKLI MÜŞTERİ İÇİN İŞLEM BİLDİRİMİ'
            # message = f'''
            # Aşağıdaki kişi/kurum için sistem üzerinde işlem yapılmak istendi ancak bu kişi/kurum yasaklı listesinde bulunduğu için işlemleri kısıtlanmıştır.

            # Kişi/Kurum Bilgileri:
            #     Tarih: {today}
            #     İsim: {obj.name}
            #     TC/VKN No: {obj.tc_vkn_no}
            #     CRM Kodu: {obj.crm_code}

            # İşlemi yapan kullanıcı:
            #     İsim: {request.user.get_full_name()}
            #     Email: {request.user.email}

            # Bu e-posta test amaçlıdır, lütfen cevap vermeyiniz.
            # '''
            # from_email = 'Arınet <noreply@arileasing.com.tr>'
            # recipient_list = ['koray.zorlu@arileasing.com.tr','arzu.sasmazer@arileasing.com.tr']

            # send_outlook_email(subject, message, from_email, recipient_list)

            return JsonResponse({'message': 'Kaydedilemedi! Bu kişi yasaklı listelerinde bulunduğu için işlemleri kısıtlanmıştır. Yöneticinizle iletişime geçin.','status':'error'}, status=400)

        # obj.types = get_partner_types(data)
        obj.name = data.get('name')
        obj.formal_name = data.get('formalName')
        # obj.vat_office = data.get('vatOffice')
        # obj.vat_no = data.get('vatNo')
        # obj.country = country if country else None
        # obj.city = city if city else None
        # obj.address = data.get('address')
        # obj.address2 = data.get('address2')
        # obj.is_billing_same = data.get('isBillingSame') or False
        # obj.billing_country = country if data.get('isBillingSame') else billing_country
        # obj.billing_city = city if data.get('isBillingSame') else billing_city
        # obj.billing_address = data.get('address') if data.get('isBillingSame') else data.get('billingAddress')
        # obj.billing_address2 = data.get('address2') if data.get('isBillingSame') else data.get('billingAddress2')
        # obj.phone_country = phone_country if data.get('phoneNumber') else None
        # obj.phone_number = data.get('phoneNumber') if phone_country else None
        # obj.email = data.get('email')
        # obj.web = data.get('web')
        # obj.about = data.get('about')
        obj.types = get_partner_types(data)
        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class ConfirmPartnerView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Partner.objects.filter(uuid = data.get('uuid')).first()

        if not obj.is_reliable_person:
            send_warning_email_for_ignored_partners({
                'name': obj.name,
                'tc_vkn_no': obj.tc_vkn_no,
                'crm_code': obj.crm_code,
                'request_user_full_name': request.user.get_full_name(),
                'request_user_email': request.user.email
            })
            return JsonResponse({'message': 'Kaydedilemedi! Bu kişi yasaklı listelerinde bulunduğu için işlemleri kısıtlanmıştır. Yöneticinizle iletişime geçin.','status':'error'}, status=400)
        

        return JsonResponse({'message': 'Yönetici onayı için Leaseflex tarafına talep gönderildi!','status':'success'}, status=200)

class IgnoePartnerView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner
    
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Partner.objects.filter(uuid = data.get('uuid')).first()
        obj.is_reliable_person = False
        obj.save()

        return JsonResponse({'message': 'İlgili kişi/kurum yasaklı listesine eklenmiştir ve Leaseflex tarafında güncellenmiştir!','status':'success'}, status=200)
class DeletePartnerView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        partner = Partner.objects.filter(uuid = data.get('uuid')).first()
        partner.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeletePartnersView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')

        for uuid in uuids:
            partner = Partner.objects.filter(uuid = uuid).first()
            partner.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class DeleteAllPartnersView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Partner

    def post(self, request, *args, **kwargs):
        partners = Partner.objects.filter()
        for partner in partners:
            partner.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)
    
class PartnersTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "static", "files", "partners-template.xlsx")
        
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class ImportPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        importer = BaseImporter(user_id=request.user.id, app="partners", model_name="Partner", file=file)

        if importer.validate_file() != 200:
            return JsonResponse(importer.validate_file(), status=400)

        send_alert({"message":"Items importing on background...",'status':'success'},room=f"private_{request.user.id}")

        df_json = importer.read_file()
        if isinstance(importer.read_file(), dict):
            return JsonResponse(df_json, status=400)
            
        importer.start_import(df_json)

        return HttpResponse(status=200)
    
class PartnerInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        crm_code = data.get('crm_code')
        
        obj = Partner.objects.filter(crm_code = crm_code).first()

        if not obj:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        partner_data = {
                'uuid': obj.uuid,
                'crm_code': obj.crm_code,
                'name': obj.name,
                'tc_vkn_no' : obj.tc_vkn_no,
                'phone_number':obj.phone_number,
                'address':obj.address,
                'city':obj.city.name if obj.city else "",
                'country':obj.country.name if obj.country else "",
                'kep':obj.kep if obj.kep else "",
                'email':obj.email,
                'is_turkkep':obj.is_turkkep
        }

        return JsonResponse({'partner':partner_data}, status=200)

class AddPartnerNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        partner = Partner.objects.select_related().filter(uuid=data.get('partner_id')).first()

        PartnerNote.objects.create(
            company = company,
            title = data.get('data').get('title'),
            text = data.get('data').get('text'),
            partner = partner,
            user = request.user
        )

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class UpdatePartnerNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = PartnerNote.objects.filter(uuid = data.get('data').get('uuid')).first()
        obj.title = data.get('data').get('title')
        obj.text = data.get('data').get('text')
        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
    
class DeletePartnerNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = PartnerNote.objects.filter(uuid = data.get('data').get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Başarıyla silindi!','status':'success'}, status=200)


class ExportPartnersView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if ExportProcess.objects.filter(user=request.user,model_name="Partner",status__in=["pending","in_progress"]).exists():
            return JsonResponse({'message':'Bu tablo için başka bir dışarı aktarma işlemi devam ediyor! Lütfen bekleyin.','status':'error'}, status=400)

        exporter = BaseExporter(
            user_id=request.user.id,
            app="partners",
            model_name="Partner",
            file_name=f"{datetime.today().strftime('%d-%m-%Y')}-partner-listesi.xlsx",
            export_url="/partners/partners_excel",
            params={"project":data.get('project')}
        )

        send_alert({"message":"Excel dosyası hazırlanıyor...",'status':'success'},room=f"private_{request.user.id}")
            
        exporter.start_export()

        return HttpResponse(status=200)

class PartnersExcelView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(self.request.user.user_companies.filter(is_active = True).first().company.uuid), "partners", "partners", "documents",f"{datetime.today().strftime('%d-%m-%Y')}-partner-listesi.xlsx")
      
        if not os.path.exists(file_path):
            return JsonResponse({'message': 'File not found!','status':'error'}, status=404)

        objs = ExportProcess.objects.filter(status = "in_progress")
        for obj in objs:
            obj.status = "completed"
            obj.save()

        return FileResponse(open(file_path, 'rb'))

###############################
#CREDIT ALLOCATION
###############################
class UpdatePartnerFinancialProfileView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = PartnerFinancialProfile
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        obj = PartnerFinancialProfile.objects.filter(uuid = data.get('uuid')).first()
        
        obj.income_types = data.get('income_types')
        obj.other_income = data.get('other_income')
        obj.fund_sources = data.get('fund_sources')
        obj.other_fund_source = data.get('other_fund_source')
        obj.sgk_job = SgkJob.objects.filter(sgk_job_code = data.get('sgk_job')).first() if data.get('sgk_job') else None
        obj.institution = data.get('institution')
        obj.position = data.get('position')
        obj.real_estate_assets_count = data.get('real_estate_assets_count')
        obj.vehicle_assets_count = data.get('vehicle_assets_count')
        obj.bank_deposit_assets = data.get('bank_deposit_assets')
        obj.investment_assets = data.get('investment_assets')
        obj.other_assets = data.get('other_assets')
        obj.transaction_amount = data.get('transaction_amount')
        obj.transaction_frequency = data.get('transaction_frequency')
        obj.transaction_risk = data.get('transaction_risk')
        obj.job_compliance = data.get('job_compliance')
        obj.customer_type = data.get('customer_type')
        obj.is_foreign_nationality = data.get('is_foreign_nationality')
        obj.is_end_beneficiary = data.get('is_end_beneficiary')
        if data.get('customer_type') == "bireysel":
            obj.is_transparency = False
            obj.is_foreign_partner = False
            obj.is_complex_partner = False
            obj.company_type = None
        else:
            obj.is_transparency = data.get('is_transparency')
            obj.is_foreign_partner = data.get('is_foreign_partner')
            obj.is_complex_partner = data.get('is_complex_partner')
            obj.company_type = data.get('company_type')
        obj.is_pep = data.get('is_pep')
        obj.is_negative_news = data.get('is_negative_news')
        obj.is_cash_payment = data.get('is_cash_payment')
        obj.is_balloon_payment = data.get('is_balloon_payment')
        obj.remitter_type = data.get('remitter_type')
        obj.is_suspicious = data.get('is_suspicious')
        obj.is_blacklisted = data.get('is_blacklisted')
        obj.is_warning_notice = data.get('is_warning_notice')
        obj.is_delayed = data.get('is_delayed')
        obj.is_kkb_score_low = data.get('is_kkb_score_low')
        obj.is_administrative_follow_up = data.get('is_administrative_follow_up')
        obj.is_cheque_risk = data.get('is_cheque_risk')
        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
