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
import time

from .models import *
from .utils.sms_utils import send_sms_with_turatel,check_sms_status
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from .utils.email_utils import send_email_with_setrow,fetch_email_reports_with_setrow

@shared_task()
def send_sms(params):
    message_result = send_sms_with_turatel(params)
    if message_result.get("message_id_list"):
        check_sms_status({"message_id_list": message_result.get("message_id_list")})

@shared_task()
def send_email_with_setrow_task(params):
    send_email_with_setrow(params)

@shared_task()
def fetch_email_reports_with_setrow_task(params):
    fetch_email_reports_with_setrow(params)