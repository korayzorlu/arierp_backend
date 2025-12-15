from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from inventory.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice

