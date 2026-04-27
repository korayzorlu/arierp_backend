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
    

class PurchaseDocument(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_documents")

    document_id = models.CharField(_("Document ID"), max_length=25, null=True, blank=True)
    code = models.CharField(_("Code"), max_length=25)
    document_number = models.CharField(_("Document Number"), max_length=140, null=True, blank=True)
    document_date = models.DateField(_("Document Date"), blank=True, null=True)

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_purchase_documents",null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_purchase_documents", null=True, blank=True)
    vendor = models.ForeignKey(Partner, on_delete=models.SET_NULL, related_name="vendor_purchase_documents", null=True, blank=True)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    vat_amount = models.DecimalField(_("Vat Amount"), default = 0.00, max_digits=14, decimal_places=2)
    total_amount = models.DecimalField(_("Total Amount"), default = 0.00, max_digits=14, decimal_places=2)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_purchase_documents")
    exchange_rate = models.DecimalField(_("Exchange Rate"), default = 0.00, max_digits=14, decimal_places=2)

    document_status = models.CharField(_("Document Status"), max_length=140, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.document_number)
    
class PurchaseDocumentItem(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_document_items")

    document_line_id = models.CharField(_("Document Line ID"), max_length=25, null=True, blank=True)
    c_type_id = models.CharField(_("C Type ID"), max_length=25, null=True, blank=True)

    purchase_document = models.ForeignKey(PurchaseDocument, on_delete=models.CASCADE, related_name="purchase_document_purchase_document_items", null=True, blank=True)
    stock_name = models.CharField(_("Stock Name"), max_length=250, null=True, blank=True)
    description = models.CharField(_("Description"), max_length=500, null=True, blank=True)
    unit_amount = models.DecimalField(_("Unit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    vat_amount = models.DecimalField(_("Vat Amount"), default = 0.00, max_digits=14, decimal_places=2)
    total_amount = models.DecimalField(_("Total Amount"), default = 0.00, max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.purchase_document.code} - {self.document_line_id}")