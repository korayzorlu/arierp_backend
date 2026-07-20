from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q
from django.db.models.functions import Lower,Upper
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import localtime, timedelta

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

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission
from leasing.models import Installment

from .serializers import *
from .filters import *

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
    
class TradeAccountList(ModelViewSet, QueryListAPIView):
    serializer_class = TradeAccountListSerializer
    filterset_class = TradeAccountFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","partner"]

        queryset = TradeAccount.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("account_id")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["partner__name","account_id","name","crm_id","crm_type"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class TradeTransactionList(ModelViewSet, QueryListAPIView):
    serializer_class = TradeTransaction1ListSerializer
    filterset_class = TradeTransactionFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    #ordering_fields = '__all__'
    #ordering_fields = list(TradeTransaction._meta.get_fields()) + ['total_tl']
    ordering_fields = [f.name for f in TradeTransaction._meta.get_fields() if hasattr(f, 'name')]
    ordering = ['posting_group_id','due_date','record_date','trade_transaction_id']
    # pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
    required_subscription = "free"
    permission_classes = [AllowAny]
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","partner","lease","currency"]
        
        queryset = TradeTransaction.objects.select_related(*custom_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            ~Q(delete_status__in=['2'])
        ).exclude(delete_status__in=['2'])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["trade_transaction_id","partner__name","lease__code","posting_group_id","posting_group_name","description","document_no","amount_type","currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class TradeTransactionForLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = TradeTransactionListSerializer
    filterset_class = TradeTransactionFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    #ordering_fields = '__all__'
    #ordering_fields = list(TradeTransaction._meta.get_fields()) + ['total_tl']
    ordering_fields = [f.name for f in TradeTransaction._meta.get_fields() if hasattr(f, 'name')]
    ordering = ['posting_group_id','due_date','record_date','trade_transaction_id']
    # pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
    required_subscription = "free"
    permission_classes = [AllowAny]
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","partner","lease","currency"]
        
        queryset = TradeTransaction.objects.select_related(*custom_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            ~Q(delete_status__in=['2'])
        ).exclude(delete_status__in=['2'])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["trade_transaction_id","partner__name","lease__code","posting_group_id","posting_group_name","description","document_no","amount_type","currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class TradeTransactionForCustomerInLeaseList(ModelViewSet, QueryListAPIView):
    queryset = TradeTransaction.objects.none()
    serializer_class = TradeTransactionForCustomerInLeaseListSerializer
    # filterset_class = TradeTransactionFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination

    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def list(self, request):
        active_company_uuid = request.query_params.get('ac')
        active_company = request.user.user_companies.filter(uuid=active_company_uuid).first()

        result = []
        
        trade_transactions = TradeTransaction.objects.select_related("company","lease","currency").filter(
            Q(company=active_company.company if active_company else None) &
            Q(lease__uuid=request.query_params.get('lease_uuid')) &
            ~Q(delete_status__in=['2']) &
            ~Q(description__icontains='Kira Ödemeleri') &
            Q(posting_group_id='1')
        ).exclude(delete_status__in=['2']).order_by('posting_group_id','due_date','record_date','trade_transaction_id')

        installments = Installment.objects.select_related("company","lease__currency").filter(
            Q(company=active_company.company if active_company else None) &
            Q(lease__uuid=request.query_params.get('lease_uuid')) &
            Q(payment_date__lte=localtime().date())
        ).order_by('sequency','payment_date')

        transaction_sequency = 1
        for trade_transaction in trade_transactions:
            result.append({
                "uuid": trade_transaction.uuid,
                "transaction_type": "trade_transaction",
                "amount_type": trade_transaction.amount_type,
                "date_obj": localtime(trade_transaction.due_date).date(),
                "date": localtime(trade_transaction.due_date).date().strftime('%d.%m.%Y'),
                "posting_group_id": trade_transaction.posting_group_id,
                "posting_group_name": trade_transaction.posting_group_name,
                "description": trade_transaction.description,
                "amount": trade_transaction.amount,
                "currency": trade_transaction.currency.code if trade_transaction.currency else None,
                "overdue_days": 0,
                "applied_status": "",
                "sequency": transaction_sequency if trade_transaction.amount_type == '0' else 0
            })
            transaction_sequency += 1

        for installment in installments:
            if installment.type == "2":
                description = "Peşinat Vadesi"
            elif installment.type == "5":
                description = "Devir Bedeli Vadesi"
            else:
                description = f"{installment.sequency}. Kira Taksiti Vadesi"

            result.append({
                "uuid": installment.uuid,
                "transaction_type": "installment",
                "amount_type": "1",
                "date_obj": installment.payment_date,
                "date": installment.payment_date.strftime('%d.%m.%Y'),
                "posting_group_id": "1",
                "posting_group_name": "Kira",
                "description": description,
                "amount": installment.amount,
                "currency": installment.lease.currency.code if installment.lease.currency else None,
                "overdue_days": (localtime().date() - installment.payment_date).days if localtime().date() > installment.payment_date else 0,
                "applied_status": "Ödenmedi",
                "sequency": 0
            })

        result.sort(key=lambda x: (x['posting_group_id'], x['date_obj'], -int(x['amount_type'])))

        for item in result:
            # if item["date_obj"] > localtime().date():
            #     balance = {
            #         "balance": "",
            #     }
            #     item["balances"] = balance
            #     continue
            objs = result
            prev_balance = 0
            group = ""
            for o in objs:
                if group != "" and group != o["posting_group_id"]:
                    prev_balance = 0
                current_amount = o["amount"] if o["amount_type"] == '1' else -o["amount"]
                prev_balance += current_amount
                if o["uuid"] == item["uuid"]:
                    balance = {
                        "balance": prev_balance,
                    }
                    break
                group = o["posting_group_id"]
            item["balances"] = balance

        remaining_amount = Decimal('0.00')
        payment_sequency = 1
        for index, item in enumerate(filter(lambda x: x["transaction_type"] == "installment", result)):
            skip = False

            payments = list(filter(lambda x: x["transaction_type"] == "trade_transaction" and x["posting_group_id"] == item["posting_group_id"] and x["amount_type"] == '0' and x["sequency"] >= payment_sequency, result))
            item_remaining = item["amount"]
            
            for payment in payments:
                remaining_amount += payment["amount"]

                if remaining_amount >= item_remaining:
                    remaining_amount -= item_remaining
                    item["overdue_days"] = (payment["date_obj"] - item["date_obj"]).days if payment["date_obj"] > item["date_obj"] else 0
                    item["applied_status"] = "Ödendi"
                    skip = True
                    payment_sequency = payment["sequency"] + 1
                    break

            if skip:
                continue



        # for index, item in enumerate(result):
        #     key_index = index + 1
        #     remaining = Decimal('0.00')

        #     while key_index < len(result):
        #         next_item = result[key_index] if key_index < len(result) else None

        #         if item["transaction_type"] == "installment":
        #             if next_item:
        #                 if item["posting_group_id"] == next_item["posting_group_id"] and next_item["amount_type"] == '0':
        #                     remaining += next_item["amount"]
        #                     if remaining >= item["amount"] and item["balances"]["balance"] <= item["amount"]:
        #                         item["overdue_days"] = (next_item["date_obj"] - item["date_obj"]).days
        #                         item["applied_status"] = "Ödendi"
        #                         break
                            
        #                     if item["date"] != next_item["date"]:
        #                         if key_index - index > 1:
        #                             if remaining >= item["amount"]:
        #                                 item["overdue_days"] = (next_item["date_obj"] - item["date_obj"]).days
        #                                 item["applied_status"] = "Ödendi"
        #                                 break
        #                             else:
        #                                 key_index += 1
        #                                 continue
        #                         elif next_item["balances"]["balance"] <= 0:
        #                             item["overdue_days"] = (next_item["date_obj"] - item["date_obj"]).days
        #                             item["applied_status"] = "Ödendi"
        #                             break
        #                         else:
        #                             key_index += 1
        #                             continue
        #                     elif item["date"] == next_item["date"]:
        #                         if next_item["balances"]["balance"] <= 0:
        #                             item["applied_status"] = "Ödendi"
        #                             break
        #                         else:
        #                             key_index += 1
        #                             continue
        #                 elif item["posting_group_id"] == next_item["posting_group_id"] and next_item["amount_type"] == '1':
        #                     key_index += 1
        #                     continue
        #                 elif next_item["posting_group_id"] != item["posting_group_id"]:
        #                     if item["balances"]["balance"] > 0:
        #                         item["overdue_days"] = (localtime().date() - item["date_obj"]).days
        #                         item["applied_status"] = "Ödenmedi"
        #                         break
        #                     else:
        #                         item["applied_status"] = "Ödendi"
        #                         break
        #             else:
        #                 if item["balances"]["balance"] > 0:
        #                     item["overdue_days"] = (localtime().date() - item["date_obj"]).days
        #                     item["applied_status"] = "Ödenmedi"
        #                     break
        #                 else:
        #                     item["applied_status"] = "Ödendi"
        #                     break
        #         key_index += 1

        return Response(result)