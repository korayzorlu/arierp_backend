from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from accounting.utils.trial_balance_utils import fetch_trial_balances_from_leaseflex

@shared_task(queue="exports")
def fetch_trial_balances(company):
    fetch_trial_balances_from_leaseflex(company)