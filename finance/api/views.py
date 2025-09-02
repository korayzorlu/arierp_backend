from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,F,ExpressionWrapper,DecimalField
from django.db.models.functions import Lower,Upper
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import now
from django.conf import settings


from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter
from rest_framework.response import Response
from rest_framework_datatables_editor.viewsets import DatatablesEditorModelViewSet, EditorModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

import traceback
from datetime import datetime,timedelta
import logging
import locale

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from .serializers import *
from .filters import *
from finance.utils import fetch_finmaks_bank_accounts,finmaks_bank_account_transactions
from common.utils.common_utils import normalize,safe_decimal



class QueryListAPIView(generics.ListAPIView):
    def get_queryset(self):
        if self.request.GET.get('format', None) == 'datatables':
            self.filter_backends = (OrderingFilter, DatatablesFilterBackend, DjangoFilterBackend)
            return super().get_queryset()
        queryset = self.queryset

        # check the start index is integer
        try:
            start = self.request.GET.get('start')
            start = int(start) if start else None
        # else make it None
        except ValueError:
            start = None

        # check the end index is integer
        try:
            end = self.request.GET.get('end')
            end = int(end) if end else None
        # else make it None
        except ValueError:
            end = None

        # skip filters and sorting if they are not exists in the model to ensure security
        accepted_filters = {}
        # loop fields of the model
        for field in queryset.model._meta.get_fields():
            # if field exists in request, accept it
            if field.name in dict(self.request.GET):
                accepted_filters[field.name] = dict(self.request.GET)[field.name]
            # if field exists in sorting parameter's value, accept it

        filters = {}

        for key, value in accepted_filters.items():
            if any(val in value for val in EMPTY_VALUES):
                if queryset.model._meta.get_field(key).null:
                    filters[key + '__isnull'] = True
                else:
                    filters[key + '__exact'] = ''
            else:
                filters[key + '__in'] = value
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all().filter(**filters)[start:end]
        return queryset

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            elif self.request.GET.get('format', None) == 'datatables':
                self._paginator = self.pagination_class()
            else:
                self._paginator = None
        return self._paginator

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class DatatablesPagination(LimitOffsetPagination):
    default_limit = 50
    limit_query_param = 'length'
    offset_query_param = 'start'

    def get_paginated_response(self, data):
        return Response({
            'draw': int(self.request.query_params.get('draw', 0)),
            'recordsTotal': self.count,
            'recordsFiltered': self.count,
            'data': data
        })
    
class BankAccountList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountListSerializer
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def list(self, request, *args, **kwargs):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
     
        USERNAME = settings.FINMAKS_USERNAME
        PASSWORD = settings.FINMAKS_PASSWORD
        INSTITUTION_CODE = "0001"
        INSTITUTION_ID = 1

        logger = logging.getLogger("django")
        try:
            bank_accounts = fetch_finmaks_bank_accounts(USERNAME,PASSWORD,INSTITUTION_CODE,INSTITUTION_ID)

            finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().all()
            currencies = Currency.objects.select_related().all()
            company_obj = active_company.company

            finmaks_bank_account_by_code = {b.bank_account_id: b for b in finmaks_bank_accounts if b.bank_account_id}
            currencies_dict = {c.code: c for c in currencies}

            for bank_account in bank_accounts:
                obj = (finmaks_bank_account_by_code.get(str(bank_account["BankAccountId"])))
                if obj:
                    obj.bank_account_id = str(bank_account["BankAccountId"]) or ""
                    obj.iban = str(bank_account["IBAN"]) or ""
                    obj.account_no = str(bank_account["AccountNo"]) or ""
                    obj.branch_code = str(bank_account["BranchCode"]) or ""
                    obj.branch_name = str(bank_account["BranchName"]) or ""
                    obj.finmaks_account_type = str(bank_account["FinmaksAccountType"]) or ""
                    obj.balance = safe_decimal(bank_account["Balance"].replace(",", ""))
                    obj.available_balance = safe_decimal(bank_account["AvailableBalance"].replace(",", ""))
                    obj.over_draft = safe_decimal(bank_account["OverDraft"].replace(",", ""))
                    obj.credit_risk = safe_decimal(bank_account["CreditRisk"].replace(",", ""))
                    obj.blocked_balance = safe_decimal(bank_account["BlockedBalance"].replace(",", ""))
                    obj.credit_limit = safe_decimal(bank_account["CreditLimit"].replace(",", ""))
                    obj.currency = currencies_dict.get("TRY" if bank_account["Currency"] == "TL" else bank_account["Currency"])
                    obj.currency_type = str(bank_account["CurrencyType"]) or ""
                    obj.bank_name = str(bank_account["BankName"]) or ""
                    obj.bank_code = str(bank_account["BankCode"]) or ""
                    obj.bank_integration_info_id = str(bank_account["BankIntegrationInfoId"]) or ""
                    obj.last_read_time = datetime.fromisoformat(bank_account["LastReadTime"])
                    obj.status = bank_account["Status"]
                    obj.save()
                else:
                    FinmaksBankAccount.objects.create(
                        company = company_obj,
                        bank_account_id = str(bank_account["BankAccountId"]) or "",
                        iban = str(bank_account["IBAN"]) or "",
                        account_no = str(bank_account["AccountNo"]) or "",
                        branch_code = str(bank_account["BranchCode"]) or "",
                        branch_name = str(bank_account["BranchName"]) or "",
                        finmaks_account_type = str(bank_account["FinmaksAccountType"]) or "",
                        balance = safe_decimal(bank_account["Balance"].replace(",", "")),
                        available_balance = safe_decimal(bank_account["AvailableBalance"].replace(",", "")),
                        over_draft = safe_decimal(bank_account["OverDraft"].replace(",", "")),
                        credit_risk = safe_decimal(bank_account["CreditRisk"].replace(",", "")),
                        blocked_balance = safe_decimal(bank_account["BlockedBalance"].replace(",", "")),
                        credit_limit = safe_decimal(bank_account["CreditLimit"].replace(",", "")),
                        currency = currencies_dict.get("TRY" if bank_account["Currency"] == "TL" else bank_account["Currency"]),
                        currency_type = str(bank_account["CurrencyType"]) or "",
                        bank_name = str(bank_account["BankName"]) or "",
                        bank_code = str(bank_account["BankCode"]) or "",
                        bank_integration_info_id = str(bank_account["BankIntegrationInfoId"]) or "",
                        last_read_time = datetime.fromisoformat(bank_account["LastReadTime"]),
                        status = bank_account["Status"],
                    )

            data = [item for item in bank_accounts if item.get("Status")]
            data = sorted(data, key=lambda x: x["BankName"])
            for item in data:
                item["Balance"] = Decimal(item["Balance"].replace(",", ""))
                item["AvailableBalance"] = Decimal(item["AvailableBalance"].replace(",", ""))
                item["BlockedBalance"] = Decimal(item["BlockedBalance"].replace(",", ""))
        except Exception as e:
            print(e)
            data = []

        data_format = request.query_params.get('format', None)

        if data_format == 'datatables':
            filter_backends = (DatatablesFilterBackend)
            data = {
                "draw": int(self.request.GET.get('draw', 1)),  # Müşteri tarafından gönderilen çizim sayısı
                "recordsTotal": len(data),  # Toplam kayıt sayısı
                "recordsFiltered": len(data),  # Filtre sonrası kayıt sayısı
                "data": data  # Gösterilecek veri
            }
            
            return Response(data)
        
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
    
class BankAccountTransactionList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountTransactionListSerializer
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def list(self, request, *args, **kwargs):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
     
        USERNAME = settings.FINMAKS_USERNAME
        PASSWORD = settings.FINMAKS_PASSWORD
        INSTITUTION_CODE = "0001"
        INSTITUTION_ID = 1
        BANK_INTEGRATION_INFO_ID = ""
        BANK_CODE = "0046"
        START_DATE = "2025-08-01"
        END_DATE = "2025-08-31"

        BASE_URL = "http://finmaks.arileasing.com.tr:92"
        ENCRYPT_PASS_ENDPOINT = "/EncryptPass"
        VIEW_ENDPOINT = "/Transactions"

        logger = logging.getLogger("django")
        try:
            bank_account_transactions = finmaks_bank_account_transactions(USERNAME,PASSWORD,INSTITUTION_CODE,INSTITUTION_ID)
            data = bank_account_transactions
            for item in data:
                item["TransactionDate"] = datetime.fromisoformat(item["TransactionDate"]).strftime("%d.%m.%Y %H:%M")
            data = sorted(data, key=lambda x: x["TransactionDate"])
        except:
            data = []

        data_format = request.query_params.get('format', None)

        if data_format == 'datatables':
            filter_backends = (DatatablesFilterBackend)
            data = {
                "draw": int(self.request.GET.get('draw', 1)),  # Müşteri tarafından gönderilen çizim sayısı
                "recordsTotal": len(data),  # Toplam kayıt sayısı
                "recordsFiltered": len(data),  # Filtre sonrası kayıt sayısı
                "data": data  # Gösterilecek veri
            }
            
            return Response(data)
        
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)