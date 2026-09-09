from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists,IntegerField,Sum,OuterRef,Subquery,ExpressionWrapper,DateField
from django.db import models
from django.utils import timezone


from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string

from leasing.models import Lease
from partners.models import Partner
from trade.models import TradeTransaction

from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr

def export_terminated_leases(self):
    objs = Lease.objects.select_related().filter(
        #vendor_filter_for_serializers(self.request.query_params) &
        Q(lease_status='feshedildi') &
        Q(is_last_project=True) &
        Q(lease_trade_transactions__posting_group_name='Fesih İadesi')
    ).annotate(
        refund_amount=Sum(
            Case(
                When(
                    lease_trade_transactions__posting_group_name='Fesih İadesi',
                    then='lease_trade_transactions__amount'
                ),
                output_field=models.DecimalField(),
            )
        )
    ).filter(
        Q(refund_amount__gt=0)
    ).exclude(contract__partner__types__contains=["special"]).distinct()

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme": [],
        "Kira Planı": [],
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Proje": [],
        "Aktifleştirme Tarihi": [],
        "Statü": [],
        "Fesih Tarihi": [],
        "Son İade Tarihi": [],
        "İade Edilecek Tutar": [],
        "PB": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        trade_transaction = TradeTransaction.objects.select_related().filter(lease = obj, posting_group_name='Fesih İadesi', amount_type='0').exclude(delete_status__in=['2']).first()
        terminated_date = timezone.localtime(trade_transaction.due_date) if obj and trade_transaction and trade_transaction.due_date else ''

        if obj and trade_transaction and trade_transaction.due_date:
            last_refund_date = timezone.localtime(trade_transaction.due_date) + timedelta(days=180)
        else:
            last_refund_date = ''

        trade_transactions_for_refund = TradeTransaction.objects.select_related().filter(lease = obj, posting_group_name='Fesih İadesi').exclude(delete_status__in=['2'])
        total_refund_amount = Decimal('0.00')
        for ttfr in trade_transactions_for_refund:
            total_refund_amount += ttfr.amount if ttfr and ttfr.amount else Decimal('0.00')
        refund_amount = total_refund_amount
    
        data["Sözleşme"].append(obj.contract.code)
        data["Kira Planı"].append(obj.code)
        data["Müşteri İsmi"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["TC/VKN No"].append(obj.contract.partner.tc_vkn_no if obj.contract.partner else "")
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Aktifleştirme Tarihi"].append(obj.activation_date if hasattr(obj, 'activation_date') else "")
        data["Statü"].append(obj.lease_status if hasattr(obj, 'lease_status') else "")
        data["Fesih Tarihi"].append(terminated_date)
        data["Son İade Tarihi"].append(last_refund_date)
        data["İade Edilecek Tutar"].append(refund_amount)
        data["PB"].append(obj.currency.code if hasattr(obj, 'currency') else "")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "İade Edilecek Tutar",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "risk", "terminated_leases", "documents")
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-fesih-edilenler.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sayfa', index=False)

        # Workbook'u al
        workbook = writer.book
        worksheet = writer.sheets['Sayfa']

        # Kolon isimlerine göre format uygula
        for idx, col in enumerate(df.columns, 1):  # enumerate 1'den başlıyor
            if col in numeric_columns:
                for cell in worksheet.iter_cols(min_col=idx, max_col=idx, min_row=2):
                    for c in cell:
                        c.number_format = '#,##0.00'   # İstediğin format
    
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()
