from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField,QuerySet, Q
from django.db.models.functions import Lower,Upper

import pandas as pd
import io
import os
from decimal import Decimal
from openai import OpenAI
from datetime import datetime
import time
import ast
import pickle

from users.models import User
from common.models import ImportProcess,Country,City,ExportProcess
from partners.models import Partner,Sector
from converters.models import BankaHareketi, BankaTahsilati, BankaTahsilatiOdoo
from leasing.utils import export_bank_activities,export_today_partners,export_tomorrow_partners,export_kdv_risk_partners,export_deposite_partners,export_delivery_confirms
from purchasing.utils import export_purchase_payments
from risk.utils.risk_partners_utils import *
from risk.utils.to_warned_risk_partners_utils import *
from risk.utils.warned_risk_partners_utils import *
from risk.utils.to_terminated_risk_partners_utils import *
from risk.utils.risk_utils import export_amount_debit_transactions
from contracts.utils.contract_utils import export_contract_payments
from operation.utils import export_partner_advance_activities,export_partner_advances

from dotenv import load_dotenv
load_dotenv()

class BaseExporter():
    allowed_extensions = ["xls", "xlsx"]
    max_file_size = 100 * 1024 * 1024
    max_rows = 10_000

    expected_columns = {
        "partner": []
    }

    def __init__(self, user_id, app, model_name, file_name, export_url, task_id=None,params=None):
        self.user = User.objects.filter(id = int(user_id)).first()
        self.app = app
        self.model_name = model_name
        self.file_name = file_name
        self.export_url = export_url
        self.model = self.get_model()
        self.task_id = task_id
        self.params = params
        self.process = None
        self.df = None

    def get_model(self):
        try:
            return apps.get_model(self.app, self.model_name)
        except LookupError:
            return None

    def start_export(self):
        from common.tasks import exportData
        exportData.delay(self.user.id, self.app, self.model_name, self.file_name, self.export_url,self.params)

    def process_export(self):
        self.process = ExportProcess.objects.create(
            company = self.user.user_companies.filter(is_active=True).first().company,
            user = self.user,
            model_name = self.model_name,
            file_name = self.file_name,
            export_url = self.export_url,
            task_id = self.task_id
        )
        self.process.save()
        
        export_function = getattr(self, f"export_{self.model_name.lower()}", None)
        if not export_function:
            self.process.status = "rejected"
            self.process.save()
            return {"message": "Sorry, something went wrong! [CM0001]"}

        export_function()

        self.process.progress = 100
        #self.process.status = "completed"
        self.process.save()
    
    def export_bankactivity(self):
        export_bank_activities(self)

    def export_todaypartner(self):
        export_today_partners(self)

    def export_riskpartner(self):
        export_risk_partners(self)

    def export_tomorrowpartner(self):
        export_tomorrow_partners(self)

    def export_riskpartnerforsms(self):
        export_risk_partners_for_sms(self)

    def export_kdvriskpartner(self):
        export_kdv_risk_partners(self)

    def export_towarnedriskpartnerforsms(self):
        export_to_warned_risk_partners_for_sms(self)

    def export_towarnedriskpartner(self):
        export_to_warned_risk_partners(self)

    def export_warnedriskpartnerforsms(self):
        export_warned_risk_partners_for_sms(self)

    def export_warnedriskpartner(self):
        export_warned_risk_partners(self)

    def export_toterminatedriskpartnerforsms(self):
        export_to_terminated_risk_partners_for_sms(self)

    def export_toterminatedriskpartner(self):
        export_to_terminated_risk_partners(self)

    def export_depositepartner(self):
        export_deposite_partners(self)

    def export_deliveryconfirm(self):
        export_delivery_confirms(self)

    def export_purchasepayment(self):
        export_purchase_payments(self)

    def export_amountdebittransaction(self):
        export_amount_debit_transactions(self)

    def export_contractpayment(self):
        export_contract_payments(self)

    def export_partneradvanceactivity(self):
        export_partner_advance_activities(self)

    def export_partneradvance(self):
        export_partner_advances(self)
