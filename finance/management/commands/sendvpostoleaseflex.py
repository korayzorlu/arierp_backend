from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from finance.models import *
from finance.tasks import fetch_partner_advances
from finance.utils.vpos_utils import send_vpos_transation_to_leaseflex_test
from finance.tasks import send_vpos_transation_to_leaseflex_task

import pandas as pd
import json
import os
import pyodbc

from zeep import Client
from zeep.transports import Transport
import requests

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
            parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")

        objs = VPosTransaction.objects.filter(company__id=int(company),status=Statuses.PENDING).order_by('process_date')

        if not objs.exists():
            print(f"No pending VPosTransaction found.")

        for obj in objs:
            print(f"Sending VPosTransaction {obj.id} to Leaseflex...")
            sent, response_message = send_vpos_transation_to_leaseflex_task.delay(obj.uuid)
            if not sent:
                obj.status = Statuses.REJECTED
                obj.last_error = response_message
                obj.save()
                print(f"Failed to send VPosTransaction {obj.ext_transaction_id}: {response_message}")
                continue

            obj.status = Statuses.SENT
            obj.response_message = response_message
            obj.save()
            print(f"VPosTransaction {obj.ext_transaction_id} sent successfully.")

        print("done!")