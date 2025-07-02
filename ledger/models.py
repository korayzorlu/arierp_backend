from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City,Currency
from partners.models import Partner

# Create your models here.

class LedgerAccount(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ledger_accounts")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_ledger_accounts", null=True, blank=True)
    account_id = models.CharField(_("Account ID"), max_length=25, blank=True, null=True)
    code = models.CharField(_("Account Code"), max_length=140, blank=True, null=True)
    name = models.CharField(_("Name"), max_length=250, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_ledger_accounts")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


