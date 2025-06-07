
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from companies.models import *

class CompanyFilter(FilterSet):
    id = CharFilter(method = 'filter_id')

    class Meta:
        model = Company
        fields = ['uuid']

    def filter_id(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
class UserCompanyFilter(FilterSet):
    id = CharFilter(method = 'filter_id')

    class Meta:
        model = UserCompany
        fields = ['uuid']

    def filter_id(self, queryset, uuid, value):
        return queryset.filter(uuid = value)