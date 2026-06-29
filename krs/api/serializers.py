from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum
from django.utils.timezone import localtime

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from krs.models import *
from contracts.models import Contract

class KapamaDetayListSerializer(serializers.Serializer):
    id = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract_header_id = serializers.IntegerField()
    contract = serializers.SerializerMethodField()
    odeme_tarihi = serializers.DateField()
    fatura_tarihi = serializers.DateField()
    kapatilan_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return Contract.objects.filter(contract_id=obj.contract_header_id).only('code').first().code if obj.contract_header_id else ''

class KapamaHareketiListSerializer(serializers.Serializer):
    id = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract_header_id = serializers.IntegerField()
    contract = serializers.SerializerMethodField()
    tarih = serializers.DateField()
    fatura_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    odeme_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    kapatilan_fatura_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    temerrut_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    bugune_kadar_temerrut = serializers.DecimalField(max_digits=14, decimal_places=2)
    odenmis_temerrut = serializers.DecimalField(max_digits=14, decimal_places=2)
    gercek_odeme_tutar = serializers.DecimalField(max_digits=14, decimal_places=2)
    protokol = serializers.DecimalField(max_digits=14, decimal_places=2)
    sentetik = serializers.BooleanField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return Contract.objects.filter(contract_id=obj.contract_header_id).only('code').first().code if obj.contract_header_id else ''
    
class KrsReportListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()
    portfoy_alt_kodu = serializers.CharField()

    uye_adi = serializers.CharField()
    olusturma_tarihi = serializers.CharField()
    bildirim_tarihi = serializers.CharField()

    hesap_numarasi = serializers.CharField()
    hesapla_iliskili_kisi_sayisi = serializers.CharField()
    doviz_kodu = serializers.CharField()
    doviz_boleni = serializers.CharField()
    ozel_talimat_gostergesi = serializers.CharField()
    acilis_tarihi = serializers.CharField()
    basvuru_referans_numarasi = serializers.CharField()
    kredi_turu = serializers.CharField()
    faiz_orani_gostergesi = serializers.CharField()
    kredi_kullanim_amaci = serializers.CharField()
    
    teminat_gostergesi = serializers.CharField()
    kredi_tutari = serializers.CharField()
    depozito_tutari = serializers.CharField()
    sozlesme_suresi = serializers.CharField()
    odeme_sikligi = serializers.CharField()
    taksit_tutari = serializers.CharField()
    son_taksit_tutari = serializers.CharField()
    taksit_sayisi = serializers.CharField()
    odeme_sekli = serializers.CharField()
    kredi_limiti = serializers.CharField()
    hesap_odeme_durumu = serializers.CharField()
    
    toplam_borc_bakiyesi = serializers.CharField()
    kredi_bakiyesi_gostergesi = serializers.CharField()
    borc_faizi_bakiyesi = serializers.CharField()
    gecikmedeki_bakiye = serializers.CharField()
    vadesinde_yapilmayan_odeme = serializers.CharField()
    son_odeme_tutari = serializers.CharField()
    son_odeme_tarihi = serializers.CharField()
    kapanis_tarihi = serializers.CharField()

    kanuni_takip_tarihi = serializers.CharField()
    tahsil_edilme_tarihi = serializers.CharField()

    kapanma_nedeni = serializers.CharField()
    hesabin_ozel_durumu = serializers.CharField()   

    yeni_hesap_numarasi = serializers.CharField()

    kalan_taksit_bakiyesi = serializers.CharField()
    taksit_tarihi_gostergesi = serializers.CharField()
    yeniden_yapilandirma_gostergesi = serializers.CharField()
    yeniden_yapilandirma_tarihi = serializers.CharField()
    tedbir_karari_gostergesi = serializers.CharField()
    kayittan_dusulen_tutar = serializers.CharField()
    nakit_cekim_tutari = serializers.CharField()
    gecikme_gun_sayisi = serializers.CharField()
    ekstre_odeme_orani = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''