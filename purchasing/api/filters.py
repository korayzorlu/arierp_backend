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

class PurchasePaymentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')

    class Meta:
        model = PurchasePayment
        fields = ['uuid']
    