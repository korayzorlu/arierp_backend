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