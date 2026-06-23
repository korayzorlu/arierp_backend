from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum,F
from django.db.models.functions import Lower,Upper,Abs

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class KapamaDetayFilter(FilterSet):

    class Meta:
        model = KapamaDetay
        fields = '__all__'

class KapamaHareketiFilter(FilterSet):

    class Meta:
        model = KapamaHareketi
        fields = '__all__'
