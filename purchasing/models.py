from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Currency, Status
from partners.models import Partner
from leasing.models import Lease

# Create your models here.
class PurchasePayment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_payments")

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_purchase_payments",null=True, blank=True)
    total_contract_amount = models.DecimalField(_("Total contract Amount"), default = 0.00, max_digits=14, decimal_places=2)
    total_vendor_payment = models.DecimalField(_("Total Vendor Payment"), default = 0.00, max_digits=14, decimal_places=2)
    before_total_payment = models.DecimalField(_("Before Total Payment"), default = 0.00, max_digits=14, decimal_places=2)
    after_total_payment = models.DecimalField(_("After Total Payment"), default = 0.00, max_digits=14, decimal_places=2)
    managing_expense = models.DecimalField(_("After Total Payment"), default = 0.00, max_digits=14, decimal_places=2)
    lease_payment_amount = models.DecimalField(_("Lease Payment Amount"), default = 0.00, max_digits=14, decimal_places=2)
    vendor_payment_with_report_date = models.DecimalField(_("Vendor Payment With Report Date"), default = 0.00, max_digits=14, decimal_places=2)
    next_payment = models.DecimalField(_("Next Payment"), default = 0.00, max_digits=14, decimal_places=2)
    purchasing = models.IntegerField(_("Purchasing"), default=0)


    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.lease.code)