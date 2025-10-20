from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict

from .models import *
from .utils.sms_utils import send_sms_with_turatel
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr

@shared_task()
def send_sms(params):
    send_sms_with_turatel(params)