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

    def export_towarnedriskpartner(self):
        export_to_warned_risk_partners(self)

    def export_depositetowarnedriskpartner(self):
        export_deposite_to_warned_risk_partners(self)

    def export_keptowarnedriskpartner(self):
        export_kep_to_warned_risk_partners(self)

    def export_postatowarnedriskpartner(self):
        export_posta_to_warned_risk_partners(self)

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

    def export_underreview(self):
        export_under_reviews(self)

    def export_purchasepayment(self):
        export_purchase_payments(self)

    def export_amountdebittransaction(self):
        export_amount_debit_transactions(self)

    def export_contractpayment(self):
        export_contract_payments(self)

    def export_partner(self):
        export_partners(self)

    def export_partneradvanceactivity(self):
        export_partner_advance_activities(self)

    def export_partneradvance(self):
        export_partner_advances(self)

    def export_activelease(self):
        export_active_leases(self)

    def export_trialbalance(self):
        export_trial_balances(self)

    def export_invoice(self):
        export_invoices(self)

    def export_finmaksbankaccountbalance(self):
        export_finmaks_bank_account_balances(self)

    def export_overduelease(self):
        export_overdue_leases(self)

    def export_warningnotice(self):
        export_warning_notices(self)

    def export_thirdperson(self):
        export_third_persons(self)

    def export_titledeedinvoicecontrol(self):
        export_title_deed_invoice_controls(self)

    def export_purchasedocument(self):
        export_purchase_documents(self)

    def export_realestate(self):
        export_real_estates(self)