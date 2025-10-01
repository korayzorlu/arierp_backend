from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import Q

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict

from .models import *
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner
from .utils.project_utils import fetch_projects_from_leaseflex

@shared_task()
def fetch_projects(company):
    fetch_projects_from_leaseflex(company)
