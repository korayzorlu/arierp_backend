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
from .utils.item_utils import fetch_items_from_leaseflex

@shared_task()
def fetch_items(company):
    fetch_items_from_leaseflex(company)