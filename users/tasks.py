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
import traceback

from .models import *
from .utils import fetch_ldap_user_info

@shared_task()
def fetch_ldap_data(company):
    try:
        users = User.objects.select_related("profile").all()

        previous_progress = 0
        for index,user in enumerate(users):
            current_progress = ((index + 1)/len(users))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            data = fetch_ldap_user_info(user.username)

            if data and len(data) > 0:
                department_value = data[0][1]["department"][0]
                if isinstance(department_value, bytes):
                    department_value = department_value.decode("utf-8")
                print(department_value)
    except Exception as e:
        print(e)
        traceback.print_exc()
