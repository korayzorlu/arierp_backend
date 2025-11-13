from django.db import models, transaction
from django.db.models import Q,IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re
from itertools import chain
from datetime import datetime,timedelta
import requests
from requests.auth import HTTPBasicAuth

from companies.models import Company
from common.models import Currency

# Create your models here.

class FinmaksBankAccount(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="finmaks_bank_accounts")

    bank_account_id = models.CharField(_("Bank Account Id"), max_length=25, null=True, blank=True)
    iban = models.CharField(_("IBAN"), max_length=50, null=True, blank=True)
    account_no = models.CharField(_("Account No"), max_length=25, null=True, blank=True)
    branch_code = models.CharField(_("Branch Code"), max_length=140, null=True, blank=True)
    branch_name = models.CharField(_("Branch Name"), max_length=250, null=True, blank=True)
    finmaks_account_type = models.CharField(_("Finmaks Account Type"), max_length=25, null=True, blank=True)

    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    available_balance = models.DecimalField(_("Available Balance"), default = 0.00, max_digits=14, decimal_places=2)
    over_draft = models.DecimalField(_("Over Draft"), default = 0.00, max_digits=14, decimal_places=2)
    credit_risk = models.DecimalField(_("Credit Risk"), default = 0.00, max_digits=14, decimal_places=2)
    blocked_balance = models.DecimalField(_("Blocked Balance"), default = 0.00, max_digits=14, decimal_places=2)
    credit_limit = models.DecimalField(_("Credit Limit"), default = 0.00, max_digits=14, decimal_places=2)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_bank_accounts")
    currency_type = models.CharField(_("Currency Type"), max_length=25, null=True, blank=True)
    bank_name = models.CharField(_("Bank Name"), max_length=25, null=True, blank=True)
    bank_code = models.CharField(_("Bank Code"), max_length=25, null=True, blank=True)
    bank_integration_info_id = models.CharField(_("Bank Integration Info Id"), max_length=25, null=True, blank=True)

    last_read_time = models.DateTimeField(_("Last Read Time"), blank=True, null=True)
    status = models.BooleanField(default=False)

    finekra_bank_account_id = models.CharField(_("Finekra Bank Account Id"), max_length=250, null=True, blank=True)
    
    is_active = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.bank_name)
    
class FinmaksTransaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="finmaks_transactions")

    bank_account = models.ForeignKey(FinmaksBankAccount, on_delete=models.CASCADE, related_name="finmaks_bank_account_finmaks_transactions", null=True, blank=True)

    transaction_id = models.CharField(_("Transaction Id"), max_length=25, null=True, blank=True)
    transaction_date = models.DateTimeField(_("Transaction Date"), blank=True, null=True)
    explanation_field = models.CharField(_("Explanation Field"), max_length=500, null=True, blank=True)
    description = models.CharField(_("Description"), max_length=500, null=True, blank=True)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    sender_vkn = models.CharField(_("Sender VKN"), max_length=25, null=True, blank=True)
    sender_iban = models.CharField(_("Sender IBAN"), max_length=50, null=True, blank=True)
    sender_account_name = models.CharField(_("SenderAccountName"), max_length=50, null=True, blank=True)
    receiver_vkn = models.CharField(_("Receiver VKN"), max_length=50, null=True, blank=True)
    receiver_iban = models.CharField(_("Receiver IBAN"), max_length=50, null=True, blank=True)
    receipt_number = models.CharField(_("Receipt Number"), max_length=50, null=True, blank=True)
    value_date = models.DateTimeField(_("Value Date"), blank=True, null=True)
    transaction_type = models.CharField(_("Transaction Type"), max_length=25, null=True, blank=True)
    bank_code = models.CharField(_("Bank Code"), max_length=25, null=True, blank=True)
    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    firm_id = models.CharField(_("Firm Id"), max_length=25, null=True, blank=True)
    firm_name = models.CharField(_("Firm Name"), max_length=25, null=True, blank=True)
    firm_merchantId = models.CharField(_("Firm Merchant Id"), max_length=25, null=True, blank=True)
    firm_externalCode = models.CharField(_("Firm External Code"), max_length=25, null=True, blank=True)
    firm_externalId = models.CharField(_("Firm ExternalId"), max_length=25, null=True, blank=True)
    transaction_branch_code = models.CharField(_("Transaction Branch Code"), max_length=25, null=True, blank=True)
    transaction_branch_name = models.CharField(_("Transaction Branch Name"), max_length=25, null=True, blank=True)
    firm_code = models.CharField(_("Firm Code"), max_length=25, null=True, blank=True)
    currency_type = models.CharField(_("Currency Type"), max_length=25, null=True, blank=True)
    debit = models.CharField(_("Debit"), max_length=25, null=True, blank=True)
    branch_code = models.CharField(_("Branch Code"), max_length=25, null=True, blank=True)
    transaction_external_id = models.CharField(_("Transaction External Id"), max_length=25, null=True, blank=True)
    external_id_used = models.BooleanField(default=False)
    external_bank_id = models.CharField(_("External Bank Id"), max_length=25, null=True, blank=True)
    reference_no = models.CharField(_("Reference No"), max_length=25, null=True, blank=True)
    finmaks_process_type = models.CharField(_("Finmaks Process Type"), max_length=25, null=True, blank=True)
    category_name = models.CharField(_("Category Name"), max_length=25, null=True, blank=True)
    integration_field_value = models.CharField(_("Category Name"), max_length=25, null=True, blank=True)
    transaction_status = models.CharField(_("Transaction Status"), max_length=25, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.transaction_id)