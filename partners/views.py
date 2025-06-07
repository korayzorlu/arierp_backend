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

from .models import *
from .tasks import importPartners
from .utils import is_valid_partner_data, get_partner_types
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.websocket_utils import send_alert

import os
import json
import pandas as pd

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

        country = Country.objects.filter(iso2 = data.get('country') if data.get('country') else 0).first()
        city = City.objects.filter(country__iso2 = data.get('country') if data.get('country') else 0,id = int(data.get('city').get("id")) if data.get('city') else 0).first()
        billing_country = Country.objects.filter(iso2 = data.get('billingCountry') if data.get('billingCountry') else 0).first()
        billing_city = City.objects.filter(country__iso2 = data.get('billingCountry') if data.get('billingCountry') else 0,id = int(data.get('billingCity').get("id")) if data.get('billingCity') else 0).first()

        phone_country = Country.objects.filter(iso2 = data.get('phoneCountry') if data.get('phoneCountry') else 0).first()

        partner = Partner.objects.filter(uuid = data.get('uuid')).first()
        partner.types = get_partner_types(data)
        partner.name = data.get('name')
        partner.formal_name = data.get('formalName')
        partner.vat_office = data.get('vatOffice')
        partner.vat_no = data.get('vatNo')
        partner.country = country if country else None
        partner.city = city if city else None
        partner.address = data.get('address')
        partner.address2 = data.get('address2')
        partner.is_billing_same = data.get('isBillingSame') or False
        partner.billing_country = country if data.get('isBillingSame') else billing_country
        partner.billing_city = city if data.get('isBillingSame') else billing_city
        partner.billing_address = data.get('address') if data.get('isBillingSame') else data.get('billingAddress')
        partner.billing_address2 = data.get('address2') if data.get('isBillingSame') else data.get('billingAddress2')
        partner.phone_country = phone_country if data.get('phoneNumber') else None
        partner.phone_number = data.get('phoneNumber') if phone_country else None
        partner.email = data.get('email')
        partner.web = data.get('web')
        partner.about = data.get('about')
        partner.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
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