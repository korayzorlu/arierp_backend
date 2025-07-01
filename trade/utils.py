from django.http import JsonResponse
from django.utils.timezone import make_aware

from datetime import datetime
import pandas as pd
import io
from decimal import Decimal

from .models import *
from common.models import Status
from partners.models import Partner

def is_valid_trade_account_data(data):
    if not data.get('account_id') or not data.get('trade_account'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def import_leases(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
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
            
           

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()