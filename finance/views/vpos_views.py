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
from finance.utils import vendor_filter_for_serializers, is_valid_vpos_transaction_data
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
        
        company = Company.objects.filter(uuid = data.get('CompanyId')).first()

        process_date = parse_datetime(data.get('ProcessDate'))
            
        currency = Currency.objects.filter(code='TRY' if data.get('CurrencyCode') == 'TL' else data.get('CurrencyCode')).first()

        obj = VPosTransaction.objects.create(
            company = company,
            process_date = process_date,
            musteri_tipi = data.get('MusteriTipi'),
            paid_amount = safe_decimal(data.get('PaidAmount')),
            currency = currency,
            lease_posting_group_id = data.get('LeasePostingGroupId'),

            firma_adi = data.get('FirmaAdi'),
            kurum_tipi = data.get('KurumTipi'),
            vergi_dairesi = data.get('VergiDairesi'),
            vergi_no = data.get('VergiNo'),
            web_sitesi = data.get('WebSitesi'),
            adres = data.get('Adres'),
            ulke = data.get('Ulke'),
            sehir = data.get('Sehir'),
            ilce = data.get('Ilce'),
            posta = data.get('Posta'),

            ad = data.get('Ad'),
            ikinci_ad = data.get('IkinciAd'),
            orta_ad = data.get('OrtaAd'),
            soyad = data.get('SoyAd'),
            cinsiyet = data.get('Cinsiyet'),
            tc_kimlik_no = data.get('TCKimlikNo'),
            pasaport_no = data.get('PasaportNo'),
            uyruk = data.get('Uyruk'),
            dogum_tarihi = data.get('DogumTarih'),
            vergi_dairesi_birey = data.get('VergiDairesi_Birey'),
            vergi_no_birey = data.get('VergiNo_Birey'),
            adres_birey = data.get('Adres_Birey'),
            ulke_birey = data.get('Ulke_Birey'),
            sehir_birey = data.get('Sehir_Birey'),
            ilce_birey = data.get('Ilce_Birey'),
            posta_birey = data.get('Posta_Birey'),

            username = data.get('UserName'),
            telefon = data.get('Telefon'),
            email = data.get('EMail'),
            fax = data.get('Fax'),
            bank_code = data.get('BankCode'),
            contract_code = data.get('ContractCode'),
            ext_transaction_id = data.get('ExtTransactionId'),
        )

        if len(data.get('IletisimList') or []) > 0 or len(data.get('IletisimList_Birey') or []) > 0:
            iletisim_list = data.get('IletisimList') or data.get('IletisimList_Birey')
            for iletisim in iletisim_list:
                VPosIletisim.objects.create(
                    vpos_transaction = obj,
                    company = obj.company,
                    iletisim_turu = iletisim.get('IletisimTuru'),
                    iletisim_degeri = iletisim.get('IletisimDegeri'),
                )

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
