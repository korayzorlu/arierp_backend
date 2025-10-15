from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from contracts.models import *
from purchasing.models import *
from purchasing.tasks import fetch_purchase_payments

from decimal import Decimal
import pandas as pd
import json
import os
import pyodbc

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
        lease = Lease.objects.filter(code = '46643.1.0').first()
        # purchase_documents = PurchaseDocument.objects.select_related().filter(lease = lease).aggregate(total_total_amount=Sum('total_amount'))
        # print(purchase_documents['total_total_amount'])

        purchase_payment = PurchasePayment.objects.select_related().filter(lease = lease).first()
        installments = purchase_payment.lease.lease_installments.select_related().filter().order_by('sequency')
        max_sequency = installments.aggregate(max_seq=Max('sequency'))['max_seq']
        installments = installments.exclude(sequency=max_sequency)
        # for installment in installments:
        #     print(
        #         f"Sequency: {installment.sequency}\n"
        #         f"  Taksit:   {installment.amount}\n"
        #         f"  Anapara:  {installment.principal}\n"
        #         f"  Ödeme:  {installment.payment}\n"
        #         f"  KDV:      {installment.vat_amount}\n"
        #         f"  Toplam:   {installment.principal + installment.vat_amount}\n"
        #         f"  KDV'li Toplam:   {installment.principal + installment.vat_amount + installment.interest}\n"
        #         "----------------------------------------"
        #     )
        installments_total = installments.select_related().filter().aggregate(
            total_amount=Sum('amount')
        )
        print((installments_total['total_amount']/Decimal('1.18'))*Decimal('1.2'))
        
        print("done!")