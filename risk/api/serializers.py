from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from risk.models import *
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
from .filters import AmountDebitTransaction
    
class AmountDebitTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    process_group = serializers.CharField()
    due_date = serializers.DateField()
    process_type = serializers.CharField()
    debit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    credit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    real_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    for_default_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    adat_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    default_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5,decimal_places=2)
    overdue_interest_rate = serializers.DecimalField(max_digits=5,decimal_places=2)
    day = serializers.IntegerField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ""
    
    def get_currency(self, obj):
        return obj.lease.currency.code if obj.lease.currency else ""