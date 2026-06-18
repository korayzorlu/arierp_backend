from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from common.models import Status,Currency
from companies.models import Company
from partners.models import Partner
from quotations.models import Quotation
from projects.models import Project

# Create your models here.



class Contract(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="contracts")

    contract_id = models.CharField(_("Contract ID"), max_length=25, null=True, blank=True)
    code = models.CharField(_("Code"), max_length=25)
    quotation_obj = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="quotation_contracts", null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_contracts", null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_contracts")
    kof = models.CharField(_("Kof"), max_length=25, null=True, blank=True)
    quotation = models.CharField(_("Quotation"), max_length=25, null=True, blank=True)
    committe = models.CharField(_("Committe"), max_length=25, null=True, blank=True)
    credit_type = models.CharField(_("Credit Type"), max_length=25, null=True, blank=True)
    customer_representative = models.CharField(_("Customer Representative"), max_length=140, null=True, blank=True)
    supplier = models.CharField(_("Supplier"), max_length=140, null=True, blank=True)
    project = models.CharField(_("Project"), max_length=250, null=True, blank=True)
    project_obj = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name="project_contracts", null=True, blank=True)
    vendor = models.ForeignKey(Partner, on_delete=models.SET_NULL, related_name="vendor_contracts", null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_contracts", null=True, blank=True)
    mkk_tesciline_gonderilecek_mi = models.BooleanField(default=False)
    kof_tan_sozlesmeye_aktarim_tarihi = models.DateTimeField(_("Kof'tan Sözleşmeye Aktarım Tarihi"), blank=True, null=True)
    lop_open_date = models.DateTimeField(_("Lop Open Date"), blank=True, null=True)
    created_date_leaseflex = models.DateTimeField(_("Created Date Leaseflex"), blank=True, null=True)

    OPERATION_STATUS_CHOICES = (
        ('tedarikcide', ('Tedarikçide')),
        ('islemde', ('İşlemde')),
        ('arsivde', ('Arşivde')),
    )
    operation_status = models.CharField(_("Operation Status"), max_length=25, default='tedarikcide', choices=OPERATION_STATUS_CHOICES, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
class ContractPayment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_contract_payments")

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_contract_payments")
    trn_id = models.CharField(_("Trn ID"), max_length=25, null=True, blank=True)
    trn_from_id = models.CharField(_("Trn From ID"), max_length=25, null=True, blank=True)
    ledger_account_id = models.CharField(_("Ledger Account ID"), max_length=25, null=True, blank=True)
    ledger_account_name = models.CharField(_("Ledger Account Name"), max_length=250, null=True, blank=True)
    trade_account_code = models.CharField(_("Trade Account Code"), max_length=25, null=True, blank=True)
    type = models.CharField(_("Type"), max_length=25, null=True, blank=True)
    source_type = models.CharField(_("Source Type"), max_length=25, null=True, blank=True) # 80 --> virtual pos
    posting_type = models.CharField(_("Posting Type"), max_length=25, null=True, blank=True)
    group_name = models.CharField(_("Group Name"), max_length=50, null=True, blank=True)
    account_code = models.CharField(_("Account Code"), max_length=25, null=True, blank=True)
    account_name = models.CharField(_("Account Name"), max_length=250, null=True, blank=True)
    date = models.DateField(_("Date"), blank=True, null=True)
    due_date = models.DateField(_("Due Date"), blank=True, null=True)
    debit_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    credit_amount = models.DecimalField(_("Credit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    local_debit_amount = models.DecimalField(_("Local Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    local_credit_amount = models.DecimalField(_("Local Credit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_contract_payments")
    exchange_rate = models.DecimalField(_("Exchange Rate"), default = 0.00, max_digits=14, decimal_places=2)
    description = models.CharField(_("Description"), max_length=1000, blank=True, null=True)
    user_name = models.CharField(_("User Name"), max_length=250, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.account_name)
    
class WarningNotice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_warning_notices")

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_warning_notices")
    document_id = models.CharField(_("Document ID"), max_length=25, null=True, blank=True)
    risk_id = models.CharField(_("Risk ID"), max_length=25, null=True, blank=True)
    customer_id = models.CharField(_("Customer ID"), max_length=25, null=True, blank=True)
    debit_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    daily_wages_date = models.DateField(_("Daily Wages Date"), blank=True, null=True)
    process_start_date = models.DateField(_("Process Start Date"), blank=True, null=True)
    service_date = models.DateField(_("Service Date"), blank=True, null=True)
    official_cancellation_date = models.DateField(_("Official Cancellation Date"), blank=True, null=True)
    paid = models.DecimalField(_("Paid"), default = 0.00, max_digits=14, decimal_places=2)
    diff = models.DecimalField(_("Diff"), default = 0.00, max_digits=14, decimal_places=2)
    state = models.CharField(_("State"), max_length=250, null=True, blank=True)
    approval_state = models.CharField(_("Approval State"), max_length=250, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.contract.code)
    
class ComprehensiveWarningNotice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_comprehensive_warning_notices")

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_comprehensive_warning_notices")
    document_id = models.CharField(_("Document ID"), max_length=25, null=True, blank=True)
    risk_id = models.CharField(_("Risk ID"), max_length=25, null=True, blank=True)
    customer_id = models.CharField(_("Customer ID"), max_length=25, null=True, blank=True)
    debit_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    daily_wages_date = models.DateField(_("Daily Wages Date"), blank=True, null=True)
    process_start_date = models.DateField(_("Process Start Date"), blank=True, null=True)
    service_date = models.DateField(_("Service Date"), blank=True, null=True)
    official_cancellation_date = models.DateField(_("Official Cancellation Date"), blank=True, null=True)
    paid = models.DecimalField(_("Paid"), default = 0.00, max_digits=14, decimal_places=2)
    diff = models.DecimalField(_("Diff"), default = 0.00, max_digits=14, decimal_places=2)
    state = models.CharField(_("State"), max_length=250, null=True, blank=True)
    approval_state = models.CharField(_("Approval State"), max_length=250, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.contract.code)
    
class TerminationWarningNotice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_termination_warning_notices")

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_termination_warning_notices")
    risk_id = models.CharField(_("Risk ID"), max_length=25, null=True, blank=True)
    customer_id = models.CharField(_("Customer ID"), max_length=25, null=True, blank=True)
    paid_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    deduction_amount = models.DecimalField(_("Debit Amount"), default = 0.00, max_digits=14, decimal_places=2)
    daily_wages_date = models.DateField(_("Daily Wages Date"), blank=True, null=True)
    process_start_date = models.DateField(_("Process Start Date"), blank=True, null=True)
    service_date = models.DateField(_("Service Date"), blank=True, null=True)
    official_cancellation_date = models.DateField(_("Official Cancellation Date"), blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.contract.code)
    
class CommitteeForm(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_committee_forms")

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_committee_forms", blank=True, null=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_committee_forms", blank=True, null=True)


    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.partner.name) if self.partner else ""