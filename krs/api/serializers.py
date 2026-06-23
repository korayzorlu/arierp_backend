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