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
from .utils.contract_utils import fetch_contracts_from_leaseflex,fetch_contract_payments_from_leaseflex,fetch_warning_notices_from_leaseflex

@shared_task()
def fetch_contracts(company):
    fetch_contracts_from_leaseflex(company)
    

@shared_task()
def fetch_contract_payments(company):
    fetch_contract_payments_from_leaseflex(company)


@shared_task()
def fetch_warning_notices(company):
    fetch_warning_notices_from_leaseflex(company)