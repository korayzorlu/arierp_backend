from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum,F

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from communication.models import *
from companies.models import Company,UserCompany
from partners.models import Partner

class SMSListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    packet_id = serializers.CharField()
    message_id = serializers.CharField()
    reference_id = serializers.CharField()
    send_date = serializers.DateTimeField()
    delivery_date = serializers.DateTimeField()
    text = serializers.CharField()
    phone_number = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''