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
from leasing.utils.export_utils import export_bank_activities,export_kdv_risk_partners,export_deposite_partners,export_delivery_confirms,export_active_leases
from purchasing.utils.common_utils import export_purchase_payments,export_purchase_documents
from risk.utils.risk_partners_utils import *
from risk.utils.to_warned_risk_partners_utils import *
from risk.utils.warned_risk_partners_utils import *
from risk.utils.to_terminated_risk_partners_utils import *
from risk.utils.today_partners_utils import *
from risk.utils.tomorrow_partners_utils import *
from risk.utils.risk_utils import export_amount_debit_transactions
from risk.utils.under_reviews_utils import export_under_reviews
from contracts.utils.contract_utils import export_contract_payments
from contracts.utils.export_utils import export_warning_notices
from operation.utils import export_partner_advance_activities,export_partner_advances
from partners.utils.common_utils import export_partners
from accounting.utils.trial_balance_utils import export_trial_balances
from accounting.utils.invoice_utils import export_invoices
from finance.utils import export_finmaks_bank_account_balances
from compliance.utils.export_utils import export_third_persons
from operation.utils import export_title_deed_invoice_controls
from projects.utils.real_estate_utils import export_real_estates

from dotenv import load_dotenv
load_dotenv()

class BaseFetcher():
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
