from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value,OuterRef,Subquery

from leasing.models import Lease
from risk.utils.risk_utils import set_risk_status,set_warning_notice_files

from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation

def import_overdue_leases(self, df_json):
    df = pd.read_json(io.StringIO(df_json), orient='records')

    leases = Lease.objects.select_related().filter(is_last_project = True)
    leases.update(overdue_days = 0)

    lease_by_code = {l.code: l for l in leases if l.code}

    required_columns = []
    empty_rows = df[required_columns].isnull().any(axis=1)
    if empty_rows.any():
        self.process.status = "rejected"
        self.process.save()
        self.process.delete()
        return

    self.process.status = "in_progress"
    self.process.items_count = len(df)
    self.process.save()
    
    previous_progress = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        obj = (lease_by_code.get(str(row['Kira Planı'])))

        if obj:
            # if not pd.isna(row['Oran']) and float(row['Oran'].replace("% ","")) >= 98 and float(row['Oran'].replace("% ","")) < 100:
            #     obj.is_kdv_diff = True
            obj.paid_rate = Decimal(str(row['Oran'].replace("% ",""))) if not pd.isna(row['Oran']) else Decimal("0.00")
            obj.total_payment = Decimal(str(row['Kdv Dahil Kira Toplamı'])) if not pd.isna(row['Kdv Dahil Kira Toplamı']) else Decimal("0.00")
            obj.paid = Decimal(str(row['Tahsilat Tutarı'])) if not pd.isna(row['Tahsilat Tutarı']) else Decimal("0.00")
            obj.overdue_amount = Decimal(str(row['Borç Bakiye'])) if not pd.isna(row['Borç Bakiye']) else Decimal("0.00")
            obj.overdue_days = int(row['Gecikme günü']) if not pd.isna(row['Gecikme günü']) else 0
            obj.overdue_0_30 = Decimal(str(row['0 - 30'])) if not pd.isna(row['0 - 30']) else Decimal("0.00")
            obj.overdue_31_60 = Decimal(str(row['31 - 60'])) if not pd.isna(row['31 - 60']) else Decimal("0.00")
            obj.overdue_61_90 = Decimal(str(row['61 - 90'])) if not pd.isna(row['61 - 90']) else Decimal("0.00")
            obj.overdue_91_120 = Decimal(str(row['91 - 120'])) if not pd.isna(row['91 - 120']) else Decimal("0.00")
            obj.overdue_121_150 = Decimal(str(row['121 - 150'])) if not pd.isna(row['121 - 150']) else Decimal("0.00")
            obj.overdue_151_180 = Decimal(str(row['151 - 180'])) if not pd.isna(row['151 - 180']) else Decimal("0.00")
            obj.overdue_181_gte = Decimal(str(row['181 >'])) if not pd.isna(row['181 >']) else Decimal("0.00")
            obj.save()

        if index == 43753:
            print(obj)

    set_risk_status("2")
    set_warning_notice_files("2",True)

    self.process.progress = 100
    self.process.status = "completed"
    self.process.save()
    
