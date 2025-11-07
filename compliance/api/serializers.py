from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from compliance.models import *
from .filters import BlackListPersonFilter
    
class BlackListPersonListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_passport_no = serializers.CharField()
    other_names = serializers.CharField()
    nationality = serializers.CharField()
    birthday = serializers.CharField()
    organization = serializers.CharField()
    date_number = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
class ScanPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    is_scan = serializers.BooleanField()
    last_scan_date = serializers.DateTimeField()
    next_scan_date = serializers.DateTimeField()
    is_reliable_person = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
class ThirdPersonListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    is_reliable_person = serializers.BooleanField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''