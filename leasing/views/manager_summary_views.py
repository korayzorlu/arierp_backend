from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max, F, ExpressionWrapper, DateField,IntegerField, Q
from django.db.models.functions import Lower,Upper,Cast
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.timezone import now

from utils.mixins import CompanyOwnershipRequiredMixin

from leasing.models import *
from leasing.utils.common_utils import is_valid_lease_data,vendor_filter_for_serializers,vendor_filter_for_views
from common.models import ImportProcess
from common.utils.import_utils import BaseImporter
from common.utils.export_utils import BaseExporter
from common.utils.websocket_utils import send_alert
from common.utils.common_utils import parse_amount
from partners.models import Partner
from contracts.models import Contract
from companies.models import UserCompany
from common.models import ExportProcess
from projects.models import Project

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

# Create your views here.

class ManagerSummaryView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company_uuid = data.get('params').get('activeCompany').get('id') if data.get('params').get('activeCompany') else None
        active_company = request.user.user_companies.filter(uuid = active_company_uuid).first()

        today = now().date()
        
        overdue_leases = Lease.objects.select_related("contract","contract__partner").prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=25) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        overdue_leases_try = Lease.objects.select_related("contract","contract__partner").prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=25) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        overdue_leases_usd = Lease.objects.select_related("contract","contract__partner").prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=25) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        overdue_leases_eur = Lease.objects.select_related("contract","contract__partner").prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=25) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        # to warned
        to_warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_warned_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_warned_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_warned_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )


        deposite_to_warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            ),
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            warning_notice_count=0,
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposite_to_warned_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        deposite_to_warned_leases_try = deposite_to_warned_leases_try.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposite_to_warned_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        deposite_to_warned_leases_usd = deposite_to_warned_leases_usd.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )
        
        deposite_to_warned_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        deposite_to_warned_leases_eur = deposite_to_warned_leases_eur.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )


        kep_to_warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        kep_to_warned_leases = kep_to_warned_leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        kep_to_warned_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        kep_to_warned_leases_try = kep_to_warned_leases_try.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        kep_to_warned_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        kep_to_warned_leases_usd = kep_to_warned_leases_usd.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        kep_to_warned_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=True) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        kep_to_warned_leases_eur = kep_to_warned_leases_eur.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )


        posta_to_warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=False) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        posta_to_warned_leases = posta_to_warned_leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        posta_to_warned_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=False) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        posta_to_warned_leases_try = posta_to_warned_leases_try.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        posta_to_warned_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=False) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        posta_to_warned_leases_usd = posta_to_warned_leases_usd.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        posta_to_warned_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_0_30__gt=0) |
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            Q(contract__partner__is_turkkep=False) &
            ~Q(contract__partner__types__contains=["special"]) &
            ~Q(contract__partner__types__contains=["barter"]) &
            ~Q(contract__partner__types__contains=["virman"])
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0)
        posta_to_warned_leases_eur = posta_to_warned_leases_eur.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        # warned
        warned_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
        ).filter(warning_notice_count__gt=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        warned_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
           Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
        ).filter(warning_notice_count__gt=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        warned_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
        ).filter(warning_notice_count__gt=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        warned_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
        ).filter(warning_notice_count__gt=0).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_terminated_leases = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_terminated_leases_try = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_terminated_leases_usd = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        to_terminated_leases_eur = Lease.objects.select_related().prefetch_related("contract__contract_warning_notices").filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposit_leases = Lease.objects.select_related("contract","contract__partner").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposit_leases_try = Lease.objects.select_related("contract","contract__partner").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "TRY") &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposit_leases_usd = Lease.objects.select_related("contract","contract__partner").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "USD") &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        deposit_leases_eur = Lease.objects.select_related("contract","contract__partner").prefetch_related().filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(data.get('params')) &
            Q(currency__code = "EUR") &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).aggregate(
            total_overdue_amount=Sum('overdue_amount'),
            count_overdue_leases=Count('id'),
            count_distinct_partners=Count('contract__partner', distinct=True)
        )

        manager_summary = [
            {   
                'id': 1,
                'title': 'Vadesi Geçmişler',
                'amount_try': float(overdue_leases_try['total_overdue_amount']) if overdue_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(overdue_leases_usd['total_overdue_amount']) if overdue_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(overdue_leases_eur['total_overdue_amount']) if overdue_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': overdue_leases['count_overdue_leases'] or 0,
                'partner': overdue_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 2,
                'title': 'İhtar Çekilecekler(Kapora)',
                'amount_try': float(deposite_to_warned_leases_try['total_overdue_amount']) if deposite_to_warned_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(deposite_to_warned_leases_usd['total_overdue_amount']) if deposite_to_warned_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(deposite_to_warned_leases_eur['total_overdue_amount']) if deposite_to_warned_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': deposite_to_warned_leases['count_overdue_leases'] or 0,
                'partner': deposite_to_warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 3,
                'title': 'İhtar Çekilecekler(Kep)',
                'amount_try': float(kep_to_warned_leases_try['total_overdue_amount']) if kep_to_warned_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(kep_to_warned_leases_usd['total_overdue_amount']) if kep_to_warned_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(kep_to_warned_leases_eur['total_overdue_amount']) if kep_to_warned_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': kep_to_warned_leases['count_overdue_leases'] or 0,
                'partner': kep_to_warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 4,
                'title': 'İhtar Çekilecekler(Posta)',
                'amount_try': float(posta_to_warned_leases_try['total_overdue_amount']) if posta_to_warned_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(posta_to_warned_leases_usd['total_overdue_amount']) if posta_to_warned_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(posta_to_warned_leases_eur['total_overdue_amount']) if posta_to_warned_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': posta_to_warned_leases['count_overdue_leases'] or 0,
                'partner': posta_to_warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 5,
                'title': 'İhtar Çekilenler',
                'amount_try': float(warned_leases_try['total_overdue_amount']) if warned_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(warned_leases_usd['total_overdue_amount']) if warned_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(warned_leases_eur['total_overdue_amount']) if warned_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': warned_leases['count_overdue_leases'] or 0,
                'partner': warned_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 6,
                'title': 'Fesih Edilecekler',
                'amount_try': float(to_terminated_leases_try['total_overdue_amount']) if to_terminated_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(to_terminated_leases_usd['total_overdue_amount']) if to_terminated_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(to_terminated_leases_eur['total_overdue_amount']) if to_terminated_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': to_terminated_leases['count_overdue_leases'] or 0,
                'partner': to_terminated_leases['count_distinct_partners'] or 0
            },
            {   
                'id': 7,
                'title': 'Kaporalar',
                'amount_try': float(deposit_leases_try['total_overdue_amount']) if deposit_leases_try['total_overdue_amount'] else 0.00,
                'amount_usd': float(deposit_leases_usd['total_overdue_amount']) if deposit_leases_usd['total_overdue_amount'] else 0.00,
                'amount_eur': float(deposit_leases_eur['total_overdue_amount']) if deposit_leases_eur['total_overdue_amount'] else 0.00,
                'quantity': deposit_leases['count_overdue_leases'] or 0,
                'partner': deposit_leases['count_distinct_partners'] or 0
            }
        ]

        return JsonResponse({'data':manager_summary}, status=200)