from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Currency, Status
from partners.models import Partner
from leasing.models import Lease

# Create your models here.
# class RiskSummary(models.Model):
#     uuid = models.UUIDField(default=uuid.uuid4, unique=True)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_payments")

#     risk_partners_total_overdue_amount = models.DecimalField(_("Risk Partners Total Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
#     risk_partners_count = models.IntegerField(_("Risk Partners Count"), default = 0)
#     risk_partners_lease_count = models.IntegerField(_("Risk Partners Lease Count"), default = 0)

#     to_warned_risk_partners_total_overdue_amount = models.DecimalField(_("To Warned Risk Partners Total Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
#     to_warned_risk_partners_count = models.IntegerField(_("To Warned Risk Partners Count"), default = 0)
#     to_warned_risk_partners_lease_count = models.IntegerField(_("To Warned Risk Partners Lease Count"), default = 0)

#     warned_risk_partners_total_overdue_amount = models.DecimalField(_("Warned Risk Partners Total Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
#     warned_risk_partners_count = models.IntegerField(_("Warned Risk Partners Count"), default = 0)
#     warned_risk_partners_lease_count = models.IntegerField(_("Warned Risk Partners Lease Count"), default = 0)

#     to_terminated_risk_partners_total_overdue_amount = models.DecimalField(_("To Terminated Risk Partners Total Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
#     to_terminated_risk_partners_count = models.IntegerField(_("To Terminated Risk Partners Count"), default = 0)
#     to_terminated_risk_partners_lease_count = models.IntegerField(_("To Terminated Risk Partners Lease Count"), default = 0)

#     created_date = models.DateTimeField(auto_now_add=True)
#     updated_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.company.name + " Risk Summary")

class AmountDebitTransaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="amount_debits")

    trn_id = models.CharField(_("Trn Id"), max_length=25, null=True, blank=True)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_amount_debits")
    process_group_id = models.CharField(_("Process Group ID"), max_length=25, null=True, blank=True)
    process_group = models.CharField(_("Process Group"), max_length=50, null=True, blank=True)
    due_date = models.DateField(_("Due Date"), blank=True, null=True)
    process_type = models.CharField(_("Process Type"), max_length=50, null=True, blank=True)

    debit_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    credit_amount = models.DecimalField(_("Credit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    real_amount = models.DecimalField(_("Real Amount"), default = 0.00, max_digits=14, decimal_places=2)
    for_default_amount = models.DecimalField(_("For Default Amount"), default = 0.00, max_digits=14, decimal_places=2)
    adat_amount = models.DecimalField(_("adat Amount"), default = 0.00, max_digits=14, decimal_places=2)
    default_amount = models.DecimalField(_("Default Amount"), default = 0.00, max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(_("Interest Rate"), default = 0.00, max_digits=5, decimal_places=2)
    overdue_interest_rate = models.DecimalField(_("Interest Rate"), default = 0.00, max_digits=14, decimal_places=2)

    day = models.IntegerField(_("Day"), default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.company.name} Amount Debit Transaction - {self.trn_id}")