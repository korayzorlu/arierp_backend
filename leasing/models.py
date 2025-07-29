from django.db import models, transaction
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re

from companies.models import Company
from common.models import Currency, Status
from contracts.models import Contract
from partners.models import Partner

# Create your models here.

def extract_contract_numbers(description):
    # Parantez içindeki tüm numaraları yakalar
    # matches = re.findall(r'sözleşme.*?\(?(\d{4,})[-–]?(\d{0,})\)?', description.lower())
    # contract_numbers = []
    # for match in matches:
    #     contract_numbers.append(match[0])
    #     if match[1]:
    #         contract_numbers.append(match[1])
    # return contract_numbers

    # if not isinstance(description, str):
    #     return []
######
    # pattern = r"""
    #     (?:
    #         sözleşme\s*no[:\s]*       # sözleşme no: 12345
    #         |
    #         sözleşme\s*[:\s]*
    #         |
    #         söz\.?\s*no[:\s]*
    #         |
    #         no[:\s]+
    #         |
    #         nolu\s+sözleşme           # 12345 nolu sözleşme
    #     )
    #     [^\d]*(\d[\d\-_]*)            # sözleşme numarası (rakam, alt çizgi, tire içerebilir)
    # """

    # matches = re.findall(pattern, description.lower(), re.VERBOSE)
    # return matches
######
    if not isinstance(description, str):
        return []

    matches = []

    # 1. sözleşme no, no:, söz. no, nolu sözleşme gibi ifadeler
    pattern_named = r"""
        (?:
            sözleşme\s*no[:\s]*       |
            sözleşme\s*[:\s]*         |
            söz\.?\s*no[:\s]*         |
            kontrat\s*no[:\s]*        |
            no[:\s]+                  |
            nolu\s+sözleşme
        )
        [^\d]*(\d[\d\-_]*)            # numara
    """
    matches += re.findall(pattern_named, description.lower(), re.VERBOSE)

    # 2. Parantez içindeki 5+ haneli numaralar
    pattern_parens = r'\((\d{5,}(?:[-_]\d{2,})*)\)'
    matches += re.findall(pattern_parens, description)

    # 3. Açıkta geçen 5-12 haneli numaralar
    pattern_standalone = r'\b(?<!\d)(\d{5,12})(?!\d)\b'
    raw_matches = re.findall(pattern_standalone, description)

    # Tekrarları ve bariz TC'leri filtrele (isteğe bağlı)
    for m in raw_matches:
        if m not in matches:
            matches.append(m)

    return matches
class Lease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="leases")

    lease_id = models.CharField(_("Lease ID"), max_length=25, null=True, blank=True)
    code = models.CharField(_("Code"), max_length=25)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_leases")
    type = models.CharField(_("Type"), max_length=25, null=True, blank=True)
    vat = models.DecimalField(_("Vat"), default = 0.00, max_digits=5, decimal_places=2)
    activation_date = models.DateField(_("Activation Date"), blank=True, null=True)

    LEASE_STATUS_CHOICES = (
        ('aktiflestirildi', ('Aktifleştirildi')),
        ('iptal_edildi', ('İptal Edildi')),
        ('devredildi', ('Devredildi')),
        ('baskasina_transfer_edildi', ('Başkasına Transfer Edildi')),
        ('planlandi', ('Planlandı')),
        ('durduruldu', ('Durduruldu')),
        ('feshedildi', ('Feshedildi')),
        ('revize_edildi', ('Revize Edildi')),
        ('pert', ('Pert')),
        ('envantere_alindi', ('Envantere Alındı')),
        ('para_birimi_degisti', ('Para Birimi Değişti')),
        ('kanuni_takibe_alindi', ('Kanuni Takibe Alındı')),
    )
    lease_status = models.CharField(_("Status"), max_length=25, default='aktiflestirildi', choices=LEASE_STATUS_CHOICES, blank=True, null=True)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_leases")
    musteri_baz_maliyet = models.DecimalField(_("Müşteri Baz Maliyet"), default = 0.00, max_digits=14, decimal_places=2)
    vade = models.IntegerField(_("Vade"), default = 0)
    leasing_rate = models.DecimalField(_("Leasing Rate"), default = 0.00, max_digits=14, decimal_places=2)
    irr = models.DecimalField(_("IRR"), default = 0.00, max_digits=14, decimal_places=2)
    total_payment = models.DecimalField(_("Total Payment"), default = 0.00, max_digits=14, decimal_places=2)
    paid = models.DecimalField(_("Paid"), default = 0.00, max_digits=14, decimal_places=2)
    paid_rate = models.DecimalField(_("Paid Rate"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_amount = models.DecimalField(_("Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_days = models.IntegerField(_("Overdue Days"), default=0)

    project_no = models.CharField(_("Project No"), max_length=25, blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_rents", null=True, blank=True)
    leasing_type = models.CharField(_("Leasing Type"), max_length=25, blank=True, null=True)
    application_no = models.CharField(_("Application No"), max_length=25, blank=True, null=True)
    is_last_project = models.BooleanField(default=False)
    current_request = models.CharField(_("Current Request"), max_length=25, blank=True, null=True)
    finansman_kurum = models.CharField(_("Finansman Kurum"), max_length=25, blank=True, null=True)
    is_tufe = models.BooleanField(default=False)
    is_musterek = models.BooleanField(default=False)
    bbsn = models.CharField(_("BBSN"), max_length=25, blank=True, null=True)

    leaseflex_automation = models.BooleanField(default=False)
    processed_amount = models.DecimalField(_("Processed Amount"), default = 0.00, max_digits=14, decimal_places=2)

    is_kdv_diff = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
class Installment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="installments")

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_installments")
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    vat = models.DecimalField(_("Vat"), default = 0.00, max_digits=5, decimal_places=2)
    vat_amount = models.DecimalField(_("Vat Amount"), default = 0.00, max_digits=14, decimal_places=2)
    payment = models.DecimalField(_("Payment"), default = 0.00, max_digits=14, decimal_places=2)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    paid = models.DecimalField(_("Paid"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_amount = models.DecimalField(_("Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
    principal = models.DecimalField(_("Principal"), default = 0.00, max_digits=14, decimal_places=2)
    interest = models.DecimalField(_("Interest"), default = 0.00, max_digits=14, decimal_places=2)
    sequency = models.PositiveIntegerField(_("Sequency"), default=0)
    lease_type = models.CharField(_("Lease Type"), max_length=50, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.lease.code)
    

    
class PartnerOverdueView(models.Model):
    partner = models.OneToOneField(Partner, on_delete=models.DO_NOTHING, primary_key=True, db_column='partner_id')
    max_overdue_days = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partner_max_overdue_days'
    
class BankActivity(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="bank_activities")

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
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_bank_activities")
    receipt_no = models.CharField(_("Receipt No"), max_length=140, blank=True, null=True)
    description = models.CharField(_("Description"), max_length=500, blank=True, null=True)
    name = models.CharField(_("Name"), max_length=500, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)

    leases = models.ManyToManyField(Lease,related_name='lease_bank_activities', blank = True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.amount)
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            super().save(*args, **kwargs)

            if is_new:
                contract_numbers = extract_contract_numbers(self.description)
                contracts = Contract.objects.filter(
                    Q(partner__tc_vkn_no=self.tc_vkn_no) & Q(code__in=contract_numbers)
                )

                for contract in contracts:
                    print(f"{contract.partner.name} - {contract.code}")
                
                leases = Lease.objects.filter(
                    (
                        Q(contract__partner__tc_vkn_no = self.tc_vkn_no) |
                        Q(contract__quotation_obj__partner__tc_vkn_no = self.tc_vkn_no) |
                        Q(contract__quotation_obj__quick_quotation__partner__tc_vkn_no = self.tc_vkn_no)
                    ) &
                    (
                        Q(lease_status = "aktiflestirildi") |
                        Q(lease_status = "planlandi") |
                        Q(lease_status = "durduruldu")
                    ) 
                ).order_by('contract_id', '-activation_date').distinct('contract_id')

                if leases:
                    for lease in leases:
                        bank_activity_lease = BankActivityLease.objects.create(
                            company = self.company,
                            bank_activity = self,
                            lease = lease
                        )

                        processed_amount = self.amount
                        
                        installments = lease.lease_installments.all()
                        total_overdue_amount = Decimal("0")
                        for installment in installments:
                            total_overdue_amount += installment.overdue_amount
                        total_overdue_amount = total_overdue_amount - lease.processed_amount #test
                        if total_overdue_amount > 0:
                            #bank_activity_lease.leaseflex_automation = True
                            if processed_amount > 0:
                                if total_overdue_amount <= processed_amount:
                                    bank_activity_lease.processed_amount = total_overdue_amount
                                    processed_amount -= total_overdue_amount
                                else:
                                    bank_activity_lease.processed_amount = processed_amount
                                    processed_amount = 0
                            # else:
                            #     bank_activity_lease.leaseflex_automation = False
                            bank_activity_lease.save()
                        bank_activity_leases = lease.lease_bank_acitivity_leases.select_related().all()
                        total_bank_activity_leases_processed_amount = Decimal("0")
                        for item in bank_activity_leases:
                            total_bank_activity_leases_processed_amount += item.processed_amount
                        lease.processed_amount = total_bank_activity_leases_processed_amount
                        lease.save()

          
    
class BankActivityLease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="bank_activity_leases")

    bank_activity = models.ForeignKey(BankActivity, on_delete=models.CASCADE, related_name="bank_activity_bank_acitivity_leases")
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_bank_acitivity_leases")
    processed_amount = models.DecimalField(_("Processed Amount"), default = 0.00, max_digits=14, decimal_places=2)
    leaseflex_automation = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.bank_activity.tc_vkn_no)
    
class PartnerOverdueView(models.Model):
    partner = models.OneToOneField(Partner, on_delete=models.DO_NOTHING, primary_key=True, db_column='partner_id')
    max_overdue_days = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partner_max_overdue_days'

