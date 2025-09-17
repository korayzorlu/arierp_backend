from django.db import models
from django.conf import settings

from django.utils.translation import gettext_lazy as _
import uuid

from underwriting.utils import check_third_person_status
from companies.models import Company
from common.models import Currency
from partners.models import Partner
from leasing.models import Lease

# Create your models here.

class PartnerAdvanceActivity(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_advance_activities")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, related_name="partner_partner_advance_activities")
    bank = models.CharField(_("Bank"), max_length=140, blank=True, null=True)
    bank_code = models.CharField(_("Bank Code"), max_length=140, blank=True, null=True)
    bank_branch_code = models.CharField(_("Bank Branch Code"), max_length=25, blank=True, null=True)
    bank_account_no = models.CharField(_("Bank Account No"), max_length=25, blank=True, null=True)

    cross_bank_code = models.CharField(_("Cross Bank Code"), max_length=140, blank=True, null=True)
    cross_bank_branch_code = models.CharField(_("Cross Bank Branch Code"), max_length=25, blank=True, null=True)
    cross_bank_account_no = models.CharField(_("Cross Bank Account No"), max_length=140, blank=True, null=True)

    process_code = models.CharField(_("Process Code"), max_length=25, blank=True, null=True)
    credit_or_debit = models.CharField(_("Credit Or Debit"), max_length=25, blank=True, null=True)
    kontrat_no = models.CharField(_("Kontrat No"), max_length=140, blank=True, null=True)

    process_date = models.DateTimeField(_("Process Date"), blank=True, null=True)
    process_date_date = models.DateField(_("Process Date Date"), blank=True, null=True)

    PROCESS_TYPE_CHOICES = (
        ('in', ('In')),
        ('out', ('Out')),
    )
    process_type = models.CharField(_("Process Type"), max_length=25, default='in', choices=PROCESS_TYPE_CHOICES, blank=True, null=True)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_partner_advance_activities")
    receipt_no = models.CharField(_("Receipt No"), max_length=140, blank=True, null=True)
    description = models.CharField(_("Description"), max_length=500, blank=True, null=True)
    name = models.CharField(_("Name"), max_length=500, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)

    is_processed = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)
    is_reliable_person = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.amount)
    
class PartnerAdvanceActivityLease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_advance_activity_leases")

    partner_advance_activity = models.ForeignKey(PartnerAdvanceActivity, on_delete=models.CASCADE, related_name="partner_advance_activity_partner_advance_activity_leases")
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="partner_advance_activity_leases")
    processed_amount = models.DecimalField(_("Processed Amount"), default = 0.00, max_digits=14, decimal_places=2,null = True, blank = True)
    leaseflex_automation = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.partner_advance_activity.tc_vkn_no)