from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum
from django.utils.timezone import localtime

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from krs.models import *
from contracts.models import Contract
from krs.utils.report_utils import make_cs0000,make_cs0100,make_cs0200,make_cs0301,make_cs9999

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
    contract_id = serializers.SerializerMethodField()
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

    satir = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ''
    
    def get_satir(self, obj):
        if obj.kayit_turu == KayitTuru.CS0000:
            print(make_cs0000(obj))
            return make_cs0000(obj)
        elif obj.kayit_turu == KayitTuru.CS0100:
            return make_cs0100(obj)
        elif obj.kayit_turu == KayitTuru.CS0200:
            return make_cs0200(obj)
        elif obj.kayit_turu == KayitTuru.CS0301:
            return make_cs0301(obj)
        elif obj.kayit_turu == KayitTuru.CS9999:
            return make_cs9999(obj)
    
class KrsReportCS0000ListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()

    uye_adi = serializers.CharField()
    olusturma_tarihi = serializers.CharField()
    bildirim_tarihi = serializers.CharField()
 
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
class KrsReportCS0100ListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()
    portfoy_alt_kodu = serializers.CharField()

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
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ''
    
class KrsReportCS0200ListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()
    portfoy_alt_kodu = serializers.CharField()

    hesap_numarasi = serializers.CharField()
    hesap_sahibinin_numarasi = serializers.CharField()
    hesap_sahibi_turu = serializers.CharField()
    birinci_kimlik_turu = serializers.CharField()
    birinci_kimlik_numarasi = serializers.CharField()
    ikinci_kimlik_turu = serializers.CharField()
    ikinci_kimlik_numarasi = serializers.CharField()
    uyruk = serializers.CharField()
    soyadi = serializers.CharField()
    soyadi_eki = serializers.CharField()
    ilk_ad_1 = serializers.CharField()
    ilk_ad_2 = serializers.CharField()
    anne_adi = serializers.CharField()
    baba_adi = serializers.CharField()
    cinsiyet = serializers.CharField()
    firma_adi = serializers.CharField()
    dogum_tarihi = serializers.CharField()
    dogum_yeri = serializers.CharField()
    kisinin_dogduru_bolge_il = serializers.CharField()
    dogum_yeri_kod = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ''
    
class KrsReportCS0301ListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()
    portfoy_alt_kodu = serializers.CharField()

    hesap_numarasi = serializers.CharField()
    hesap_sahibinin_numarasi = serializers.CharField()
    ozel_talimat_gostergesi = serializers.CharField()
    adres_tipi = serializers.CharField()
    simdiki_onceki_adres_gostergesi = serializers.CharField()
    adrese_tasindigi_tarih = serializers.CharField()
    adresten_ayrildigi_tarih = serializers.CharField()
    satir_1 = serializers.CharField()
    satir_2 = serializers.CharField()
    satir_3 = serializers.CharField()
    satir_4 = serializers.CharField()
    posta_kodu = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ''
    
class KrsReportCS9999ListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    kayit_turu = serializers.CharField()
    versiyon = serializers.CharField()
    uye_kodu = serializers.CharField()
    portfoy_kodu = serializers.CharField()
    hesap_kayitlarinin_toplam_sayisi = serializers.CharField()
    diger_para_birimine_gore_hesap_kayitlarinin_toplam_sayisi = serializers.CharField()
    hesap_gecmisi_kayitlarinin_toplam_sayisi = serializers.CharField()
    isim_kayitlarinin_toplam_sayisi = serializers.CharField()
    formatlanmamis_adres_kayitlarinin_toplam_sayisi = serializers.CharField()
    detayli_kisisel_bilgiler_kayitlarinin_toplam_sayisi = serializers.CharField()
    detayli_isveren_bilgileri_kayitlarinin_toplam_sayisi = serializers.CharField()
    detayli_banka_bilgileri_kayitlarinin_toplam_sayisi = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''