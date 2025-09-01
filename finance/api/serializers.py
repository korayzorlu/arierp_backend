from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from finance.models import *
from companies.models import Company,UserCompany
    
class BankAccountListSerializer(serializers.Serializer):
    BankAccountId = serializers.CharField()
    IBAN = serializers.CharField()
    AccountNo = serializers.CharField()
    BranchCode = serializers.CharField()
    BranchName = serializers.CharField()
    FinmaksAccountType = serializers.CharField()
    Balance = serializers.CharField()
    AvailableBalance = serializers.CharField()
    OverDraft = serializers.CharField()
    CreditRisk = serializers.CharField()
    BlockedBalance = serializers.CharField()
    CreditLimit = serializers.CharField()
    Currency = serializers.CharField()
    CurrencyType = serializers.CharField()
    BankName = serializers.CharField()
    BankCode = serializers.CharField()
    BankIntegrationInfoId = serializers.CharField()
    LastReadTime = serializers.CharField()
    Status = serializers.CharField()