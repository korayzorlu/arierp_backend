from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class ProjectFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    code = CharFilter(method = 'filter_code')
    project_id = CharFilter(method = 'filter_project_id')
    partner_crm_code = CharFilter(method = 'filter_partner_crm_code')
    name = CharFilter(method = 'filter_name')

    class Meta:
        model = Project
        fields = ['uuid','project_id','name']
    
    def filter_partner_crm_code(self, queryset, partner_crm_code, value):
        return queryset.filter(partner_crm_code = value)
    