from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists,F,IntegerField
from django.db.models.functions import Lower,Upper,Cast
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import now
from django.db.models.functions import TruncDate

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
from dateutil.relativedelta import relativedelta

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission
from common.api.views import QueryListAPIView,DatatablesPagination

from .serializers import *
from .filters import *

class RealEstateAgentList(ModelViewSet, QueryListAPIView):
    serializer_class = RealEstateAgentListSerializer
    filterset_class = RealEstateAgentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = [
        'name','phone_number_1','phone_number_2','url'
    ]
    ordering = ['-created_date']
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
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = RealEstateAgent.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["name","phone_number_1","phone_number_2","url"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class WhatsappMessageList(ModelViewSet, QueryListAPIView):
    serializer_class = WhatsappMessageListSerializer
    filterset_class = WhatsappMessageFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = [
        'real_estate_agent__name','real_estate_agent__phone_number_1','real_estate_agent__phone_number_2','real_estate_agent__url'
    ]
    ordering = ['-created_date']
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
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company","real_estate_agent"]

        queryset = WhatsappMessage.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["real_estate_agent__name","real_estate_agent__phone_number_1","real_estate_agent__phone_number_2","real_estate_agent__url"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
