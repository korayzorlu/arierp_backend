from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Currency, Status
from partners.models import Partner

# Create your models here.

class QuickQuotation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="quick_quotations")

    code = models.CharField(_("Code"), max_length=25)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_quick_quotations", null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_quick_quotations", null=True, blank=True)
    quotation_no = models.CharField(_("Quotation No"), max_length=25, null=True, blank=True)

    customer_type = models.CharField(_("Customer Type"), max_length=25, null=True, blank=True)
    project = models.CharField(_("Project"), max_length=250, null=True, blank=True)
    block = models.CharField(_("Block"), max_length=25, null=True, blank=True)
    unit = models.CharField(_("Unit"), max_length=25, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_quick_quotations")
    price = models.DecimalField(_("Price"), default = 0.00, max_digits=14, decimal_places=2)
    vat = models.DecimalField(_("Vat"), default = 0.00, max_digits=5, decimal_places=2)

    customer_signature_date = models.DateField(_("Customer Signature Date"), blank=True, null=True)
    unit_delivery_date = models.DateField(_("Unit Delivery Date"), blank=True, null=True)
    is_tufe = models.BooleanField(default=False)
    ortalama_tahsil_suresi = models.DecimalField(_("Ortalama Tahsil Süresi"), default = 0.00, max_digits=8, decimal_places=2)
    devremulk = models.CharField(_("Devremulk"), max_length=25, null=True, blank=True)
    start_date = models.DateField(_("StartDate"), blank=True, null=True)
    finish_date = models.DateField(_("Finish Date"), blank=True, null=True)
    bbsn = models.CharField(_("BBSN"), max_length=25, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)

class Quotation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="quotations")

    code = models.CharField(_("Code"), max_length=25)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_quotations", null=True, blank=True)
    quick_quotation = models.ForeignKey(QuickQuotation, on_delete=models.CASCADE, related_name="quick_quotation_quotations", null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, related_name="partner_quotations", null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_quotations")
    kbm = models.DecimalField(_("KBM"), default = 0.00, max_digits=14, decimal_places=2)

    customer_representative = models.CharField(_("Customer Representative"), max_length=140, null=True, blank=True)
    kof = models.CharField(_("Kof"), max_length=25, null=True, blank=True)
    request_date = models.DateField(_("Request Date"), blank=True, null=True)
    rev_date = models.DateField(_("Rev Date"), blank=True, null=True)
    supplier = models.CharField(_("Supplier"), max_length=250, null=True, blank=True)
    project = models.CharField(_("Project"), max_length=250, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
