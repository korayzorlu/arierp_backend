from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City, Currency
from partners.models import Partner
from leasing.models import Lease

# Create your models here.

class TradeAccount(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="trade_accounts")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_trade_accounts", null=True, blank=True)
    account_id = models.CharField(_("Account ID"), max_length=25, blank=True, null=True)
    crm_id = models.CharField(_("CRM ID"), max_length=25, blank=True, null=True)
    crm_type = models.CharField(_("CRM Type"), max_length=25, blank=True, null=True)

    name = models.CharField(_("Name"), max_length=140, null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
# class Collection(models.Model):
#     uuid = models.UUIDField(default=uuid.uuid4, unique=True)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="trade_accounts")

#     partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_trade_accounts", null=True, blank=True)
#     account_id = models.CharField(_("Account ID"), max_length=25, blank=True, null=True)
#     crm_id = models.CharField(_("CRM ID"), max_length=25, blank=True, null=True)
#     crm_type = models.CharField(_("CRM Type"), max_length=25, blank=True, null=True)

#     name = models.CharField(_("Name"), max_length=140, null=True, blank=True)
    
#     created_date = models.DateTimeField(auto_now_add=True)
#     updated_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)

class TradeTransaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="trade_transactions")

    trade_transaction_id = models.CharField(_("Trade Transaction ID"), max_length=50, null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_trade_transactions", null=True, blank=True)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_trade_transactions", null=True, blank=True)
    posting_group_id = models.CharField(_("Posting Group ID"), max_length=50, null=True, blank=True)
    posting_group_name = models.CharField(_("Posting Group Name"), max_length=140, null=True, blank=True)
    description = models.CharField(_("Description"), max_length=1000, null=True, blank=True)
    document_no = models.CharField(_("Document No"), max_length=140, null=True, blank=True)
    amount_type = models.CharField(_("Amount Type"), max_length=50, null=True, blank=True)

    due_date = models.DateTimeField(_("Due Date"), blank=True, null=True)
    record_date = models.DateTimeField(_("Record Date"), blank=True, null=True)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_trade_transactions")
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    local_amount = models.DecimalField(_("Local Amount"), default = 0.00, max_digits=14, decimal_places=2)
    exchange_rate = models.DecimalField(_("Exchange Rate"), default = 0.00, max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.trade_transaction_id}")  