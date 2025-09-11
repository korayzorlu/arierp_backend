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