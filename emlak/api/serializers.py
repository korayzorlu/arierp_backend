from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum
from django.utils.timezone import localtime

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from emlak.models import *

class RealEstateAgentListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    phone_number_1 = serializers.CharField()
    phone_number_2 = serializers.CharField()
    url = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

class WhatsappMessageListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    real_estate_agent = serializers.SerializerMethodField()
    phone_number_1 = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    ilan_no = serializers.CharField()
    text = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_real_estate_agent(self, obj):
        return obj.real_estate_agent.name if obj.real_estate_agent else ''

    def get_phone_number_1(self, obj):
        return obj.real_estate_agent.phone_number_1 if obj.real_estate_agent and obj.real_estate_agent.phone_number_1 else ''