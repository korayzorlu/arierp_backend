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