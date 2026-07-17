from django.db import models, transaction
from django.db.models import Q,IntegerField,Count,Max,Case,When,F,Value,DateField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re
from itertools import chain
from datetime import datetime,timedelta
import requests
from requests.auth import HTTPBasicAuth
import ollama

from common.utils.common_utils import catch_name_from_description
from underwriting.utils import check_third_person_status
from companies.models import Company
from common.models import Currency, Status
from common.utils.ai_utils import EXAMPLE_DEF,EXAMPLE_LIST
from contracts.models import Contract
from partners.models import Partner
from finance.models import FinmaksTransaction
from inventory.models import Item
from quotations.models import Quotation
from compliance.utils.third_person_utils import create_third_person
from risk.utils.filter_utils import gecikmede_filters,ihtar_cekilecek_filters,ihtar_cekildi_filters,fesih_edilecek_filters
from projects.models import RealEstate

from .utils.common_utils import extract_contract_numbers,extract_contract_numberss
from .utils.bank_activity_utils import (
    distribude_amount_with_leases,
    match_bank_activity_from_iban,
    matched_leases_with_contract_numbers,
    matched_partner_with_tc_vkn_no,
    add_bank_activity_leases,
    match_bank_activity_leases,
    distribute_amount,
    matched_leases_with_amount
)

# Create your models here.
class RiskStatus(models.TextChoices):
    RISK_YOK = 'risk_yok', 'Risk Yok'
    GECIKMEDE = 'gecikmede', 'Gecikmede'
    IHTAR_CEKILECEK = 'ihtar_cekilecek', 'İhtar Çekilecek'
    IHTAR_CEKILDI = 'ihtar_cekildi', 'İhtar Çekildi'
    FESIH_EDILECEK = 'fesih_edilecek', 'Fesih Edilecek'

class Lease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="leases")

    lease_id = models.CharField(_("Lease ID"), max_length=25, null=True, blank=True)
    main_lease_id = models.CharField(_("Main Lease ID"), max_length=25, null=True, blank=True)
    code = models.CharField(_("Code"), max_length=25)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_leases")
    real_estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, related_name="real_estate_leases", null=True, blank=True)
    type = models.CharField(_("Type"), max_length=25, null=True, blank=True)
    vat = models.DecimalField(_("Vat"), default = Decimal("0.00"), max_digits=5, decimal_places=2)
    activation_date = models.DateField(_("Activation Date"), blank=True, null=True)
    signature_date = models.DateField(_("Signature Date"), blank=True, null=True)

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
    lease_status_update_date = models.DateTimeField(_("Lease Status Update Date"), blank=True, null=True)
    
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_leases")
    musteri_baz_maliyet = models.DecimalField(_("Müşteri Baz Maliyet"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    operasyon_baz_maliyet = models.DecimalField(_("Operasyon Baz Maliyet"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    vade = models.IntegerField(_("Vade"), default = 0)
    leasing_rate = models.DecimalField(_("Leasing Rate"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    irr = models.DecimalField(_("IRR"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(_("Interest Rate"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    total_payment = models.DecimalField(_("Total Payment"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    paid = models.DecimalField(_("Paid"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    paid_rate = models.DecimalField(_("Paid Rate"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_amount = models.DecimalField(_("Overdue Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_days = models.IntegerField(_("Overdue Days"), default=0)
    overdue_0_30 = models.DecimalField(_("Overdue 0 - 30"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_31_60 = models.DecimalField(_("Overdue 31 - 60"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_61_90 = models.DecimalField(_("Overdue 61 - 90"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_91_120 = models.DecimalField(_("Overdue 91 - 120"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_121_150 = models.DecimalField(_("Overdue 121 - 150"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_151_180 = models.DecimalField(_("Overdue 151 - 180"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_181_gte = models.DecimalField(_("Overdue 181 >"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    first_installment_date = models.DateField(_("First Installment Date"), blank=True, null=True)
    odenmesi_gereken_yerel = models.DecimalField(_("Ödenmesi Gereken Yerel"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    odenmesi_gereken_usd = models.DecimalField(_("Ödenmesi Gereken USD"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    odenen_yerel = models.DecimalField(_("Ödenen Yerel"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    odenen_usd = models.DecimalField(_("Ödenen USD"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    geciken_usd = models.DecimalField(_("Geciken USD"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    geciken_odenmesi_gereken_usd = models.DecimalField(_("Geciken Ödenmesi Gereken USD"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    kur_kaybi = models.DecimalField(_("Kur Kaybı"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    kur_kaybi_yuzde = models.DecimalField(_("Kur Kaybı Yüzde"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufeli_geciken = models.DecimalField(_("Tüfeli Geciken"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_endeks = models.DecimalField(_("Tüfe Endeks"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_ana_endeks = models.DecimalField(_("Tüfe Ana Endeks"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_tahsilat_endeks = models.DecimalField(_("Tüfe Tahsilat Endeks"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_odenmesi_gereken = models.DecimalField(_("Tüfe Ödenmesi Gereken"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_odenen = models.DecimalField(_("Tüfe Ödenen"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_fark = models.DecimalField(_("Tüfe Fark"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    tufe_reel_fark = models.DecimalField(_("Tüfe Reel Fark"), default = Decimal("0.00"), max_digits=14, decimal_places=2)

    paid_amount = models.DecimalField(_("Paid Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    installment_amount = models.DecimalField(_("Total Installment Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    transfer_amount = models.DecimalField(_("Transfer Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)

    purchase_document_amount = models.DecimalField(_("Purchase Document Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)

    item = models.ForeignKey(Item, on_delete=models.SET_NULL, blank=True, null=True, related_name="project_leases")
    block = models.CharField(_("Block"), max_length=50, null=True, blank=True)
    unit = models.CharField(_("Unit"), max_length=50, null=True, blank=True)
    period = models.CharField(_("Period"), max_length=50, null=True, blank=True)
    island = models.CharField(_("Island"), max_length=50, null=True, blank=True)
    parcel = models.CharField(_("Parcel"), max_length=50, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    district = models.CharField(_("District"), max_length=50, null=True, blank=True)
    vendor = models.ForeignKey(Partner, on_delete=models.SET_NULL, blank=True, null=True, related_name="vendor_leases")
    project_no = models.CharField(_("Project No"), max_length=25, blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_rents", null=True, blank=True)
    leasing_type = models.CharField(_("Leasing Type"), max_length=25, blank=True, null=True)
    application_no = models.CharField(_("Application No"), max_length=25, blank=True, null=True)
    is_last_project = models.BooleanField(default=False)
    is_last_project_arinet = models.BooleanField(default=False)
    current_request = models.CharField(_("Current Request"), max_length=25, blank=True, null=True)
    finansman_kurum = models.CharField(_("Finansman Kurum"), max_length=25, blank=True, null=True)
    is_tufe = models.BooleanField(default=False)
    is_musterek = models.BooleanField(default=False)
    bbsn = models.CharField(_("BBSN"), max_length=25, blank=True, null=True)
    crm_no = models.CharField(_("CRM No"), max_length=25, blank=True, null=True)
    ifs_tahsilat = models.DecimalField(_("IFS Tahsilat"), default = Decimal("0.00"), max_digits=14, decimal_places=2)

    leaseflex_automation = models.BooleanField(default=False)
    processed_amount = models.DecimalField(_("Processed Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    is_processed = models.BooleanField(default=False)

    is_kdv_diff = models.BooleanField(default=False)
    is_agreed_terminated = models.BooleanField(default=False)
    is_credit = models.BooleanField(default=False)
    is_under_review = models.BooleanField(default=False)
    is_not_invoice = models.BooleanField(default=False)
    is_lop_revision = models.BooleanField(default=False)
    
    WARNING_NOTICE_STATUS_CHOICES = (
        ('ihtar_yok', ('İhtar Yok')),
        ('normal_ihtar', ('Notrmal İhtar')),
        ('kapsamli_ihtar', ('Kapsamlı İhtar')),
    )
    warning_notice_status = models.CharField(_("Status"), max_length=25, default='ihtar_yok', choices=WARNING_NOTICE_STATUS_CHOICES, blank=True, null=True)

    terminated_date = models.DateField(_("Terminated Date"), blank=True, null=True)
    notary_public_date = models.DateField(_("Notary Public Date"), blank=True, null=True)

    transfer_count = models.PositiveIntegerField(_("Transfer Count"), default=0)
    is_delivery = models.BooleanField(default=False)
    is_title_deed_delivered = models.BooleanField(default=False)

    #ifs-crm
    crm_contract_code = models.CharField(_("CRM Contract Code"), max_length=25, blank=True, null=True)
    crm_project_id = models.CharField(_("CRM Project ID"), max_length=25, blank=True, null=True)
    crm_bbsn = models.CharField(_("CRM BBSN"), max_length=25, blank=True, null=True)
    crm_durum = models.CharField(_("CRM Durum"), max_length=25, blank=True, null=True)
    crm_satici = models.CharField(_("CRM Satici"), max_length=250, blank=True, null=True)
    crm_invoice_date = models.DateField(_("CRM Invoice Date"), blank=True, null=True)
    crm_invoice_no = models.CharField(_("CRM Invoice No"), max_length=50, blank=True, null=True)
    crm_invoice_amount = models.DecimalField(_("CRM Invoice Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    crm_invoice_kdv_amount = models.DecimalField(_("CRM Invoice KDV Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    crm_invoice_total_amount = models.DecimalField(_("CRM Invoice Total Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    #ifs-crm-end

    #arinet
    ari_bbsn = models.CharField(_("Arı BBSN"), max_length=25, blank=True, null=True)
    #arinet-end

    #risk
    risk_status = models.CharField(_("Risk Status"), max_length=25, default=RiskStatus.RISK_YOK, choices=RiskStatus.choices, blank=True, null=True)
    #risk-end

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

            #===========================
            # RISK STATUS UPDATE
            #===========================
            # if Lease.objects.filter(
            #     Q(pk=self.pk) &
            #     gecikmede_filters()
            # ).exists():
            #     print(self.code)
            #     self.risk_status = RiskStatus.GECIKMEDE
            #     super().save(update_fields=['risk_status'])
            # elif Lease.objects.filter(
            #     Q(pk=self.pk) &
            #     ihtar_cekilecek_filters()
            # ).exists():
            #     self.risk_status = RiskStatus.IHTAR_CEKILECEK
            #     super().save(update_fields=['risk_status'])
            # elif Lease.objects.filter(
            #     Q(pk=self.pk) &
            #     ihtar_cekildi_filters()
            # ).annotate(
            #     warning_notice_count=Count(
            #         'contract__contract_warning_notices',
            #         distinct=True,
            #         filter=Q(contract__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
            #     ),
            # ).filter(warning_notice_count__gt=0).exists():
            #     self.risk_status = RiskStatus.IHTAR_CEKILDI
            #     super().save(update_fields=['risk_status'])
            # elif Lease.objects.filter(
            #     Q(pk=self.pk) &
            #     fesih_edilecek_filters()
            # ).annotate(
            #     official_cancellation_date=Max(
            #         Case(
            #             When(
            #                 Q(contract__contract_warning_notices__state__in=['Yeni', 'Geçerli']) &
            #                 Q(contract__contract_warning_notices__official_cancellation_date__lte=now().date()),
            #                 then=F('contract__contract_warning_notices__official_cancellation_date')
            #             ),
            #             default=None,
            #             output_field=DateField()
            #         )
            #     ),
            # ).filter(official_cancellation_date__lte=now().date()).exists():
            #     self.risk_status = RiskStatus.FESIH_EDILECEK
            #     super().save(update_fields=['risk_status'])


            from .utils.lease_utils import check_risk_status
            if check_risk_status(self) != self.risk_status:
                self.risk_status = check_risk_status(self)
                super().save(update_fields=['risk_status'])
            #===========================
            # RISK STATUS UPDATE END
            #===========================
    
class LeaseNote(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="lease_notes")

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, blank=True, null=True, related_name="lease_lease_notes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="user_lease_notes")
    title = models.CharField(_("Title"), max_length=140, blank=True, null=True)
    text = models.CharField(_("Text"), max_length=1000, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.user.get_full_name()} - {self.title}")
    
class Installment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="installments")

    installment_id = models.CharField(_("Installment ID"), max_length=25, null=True, blank=True)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_installments")
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    vat = models.DecimalField(_("Vat"), default = Decimal("0.00"), max_digits=5, decimal_places=2)
    vat_amount = models.DecimalField(_("Vat Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    payment = models.DecimalField(_("Payment"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    amount = models.DecimalField(_("Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    paid = models.DecimalField(_("Paid"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    overdue_amount = models.DecimalField(_("Overdue Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    principal = models.DecimalField(_("Principal"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    balance = models.DecimalField(_("Balance"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    interest = models.DecimalField(_("Interest"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    sequency = models.PositiveIntegerField(_("Sequency"), default=0)
    lease_type = models.CharField(_("Lease Type"), max_length=50, blank=True, null=True)
    TYPE_CHOICES = (
        ('1', ('Kira')),
        ('2', ('Peşinat')),
        ('3', ('Küçük Kira')),
        ('4', ('Ödemesiz')),
        ('5', ('Devir Bedeli')),
        ('6', ('Reeskont')),
        ('7', ('Sadece Faiz')),
    )
    type = models.CharField(_("Payment Type"), max_length=25, default='1', choices=TYPE_CHOICES, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.lease.code)
    

    
# class PartnerOverdueView(models.Model):
#     partner = models.OneToOneField(Partner, on_delete=models.DO_NOTHING, primary_key=True, db_column='partner_id')
#     max_overdue_days = models.IntegerField()

#     class Meta:
#         managed = False
#         db_table = 'partner_max_overdue_days'
    
class BankActivity(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="bank_activities")

    finmaks_transaction = models.ForeignKey(FinmaksTransaction, on_delete=models.CASCADE, null=True, blank=True, related_name="finmaks_transaction_bank_activities")
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
    amount = models.DecimalField(_("Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_bank_activities")
    receipt_no = models.CharField(_("Receipt No"), max_length=140, blank=True, null=True)
    description = models.CharField(_("Description"), max_length=500, blank=True, null=True)
    name = models.CharField(_("Name"), max_length=500, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)
    card_no = models.CharField(_("Card No"), max_length=50, null=True, blank=True)

    leases = models.ManyToManyField(Lease, related_name='lease_bank_activities', blank=True, editable=False)

    is_vpos = models.BooleanField(default=False)
    is_certain = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)
    is_reliable_person = models.BooleanField(default=False)
    
    THIRD_PERSON_STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('cleared', ('Cleared')),
        ('flagged', ('Flagged')),
        ('need_document', ('Need Document')),
    )
    third_person_status = models.CharField(_("Third Person Status"), max_length=25, default='pending', choices=THIRD_PERSON_STATUS_CHOICES, blank=True, null=True)

    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.description)
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            super().save(*args, **kwargs)

            if is_new:
                ####AI TEST####

                # response = settings.AI_CLIENT.generate(
                #     model="gpt-oss:20b",
                #     prompt=f"""
                #         {EXAMPLE_LIST}
                        
                #         Using this list as reference, try to find only the contract number(s) from the description below.
                #         Sometimes customers write contract numbers with dots (for example, 48.152). Contract numbers are usually 4-7 digit numbers and do not contain punctuation marks in between. Exceptionally, for revised contracts, if the contract number is 65789, after revision it may appear as 65789/1. Only this format change is allowed.
                #         Also, do not consider the last number if it is an identity number.
                #         Also, some descriptions may contain more than one contract number. Try to find all contract numbers.
                #         If you find contract numbers, provide them only as a list. Write the contract numbers as strings. If you cannot find any, return an empty list. Do not write anything else.
                            
                #         Description:

                #         '{self.description}'
                #     """,
                #     options={
                #         "num_thread": 4
                #     }
                # )

                # print(response["response"])
                # print(type(response["response"]))

                #response = extract_contract_numbers(self.description)
                #print(f"Extracted contract numbers: {response}")

                ####AI TEST END####

                ####NEW MATCHING SYSTEM####
                matched_partner = matched_partner_with_tc_vkn_no({
                    "tc_vkn_no": self.tc_vkn_no
                })

                if matched_partner:
                    matched_contract_numbers = extract_contract_numbers(self.description)
                    if matched_contract_numbers == "kapora":
                        bank_activity_leases = add_bank_activity_leases({
                            "company": self.company,
                            "partner": matched_partner,
                            "bank_activity": self,
                        })
                        
                        self.is_certain = False
                        super().save(update_fields=['is_certain'])
                        return
                    if matched_contract_numbers:
                        self.is_certain = True
                        super().save(update_fields=['is_certain'])
                    matched_leases = matched_leases_with_contract_numbers({
                        "partner": matched_partner,
                        "contract_numbers": matched_contract_numbers
                    })
                    if not matched_leases:
                        matched_leases = matched_leases_with_amount({
                            "partner": matched_partner,
                            "amount": self.amount
                        })
                        print(f"matched_leases_2: {matched_leases}")
                    bank_activity_leases = add_bank_activity_leases({
                        "company": self.company,
                        "partner": matched_partner,
                        "bank_activity": self,
                    })
                    matched_bank_activity_leases = match_bank_activity_leases({
                        "bank_activity_leases": bank_activity_leases,
                        "leases": matched_leases
                    })
                    #print(f"matched_bank_activity_leases: {matched_bank_activity_leases}")
                    if matched_contract_numbers:
                        remaining_amount = distribute_amount({
                            "is_certain": self.is_certain,
                            "bank_activity_leases": matched_bank_activity_leases,
                            "total_amount": self.amount
                        })
                    else:
                        remaining_amount = distribude_amount_with_leases({
                            "is_certain": self.is_certain,
                            "bank_activity_leases": bank_activity_leases,
                            "total_amount": self.amount
                        })
                        
                    #print(f"remaining_amount: {remaining_amount}")

                else:
                    scan_result = check_third_person_status(self)
                    #print(scan_result)
                    third_person = create_third_person(self,scan_result)
                    if scan_result["status"] == 'cleared':
                        if third_person["is_new"]:
                            self.third_person_status = 'need_document'
                        else:
                            self.third_person_status = 'cleared' if third_person["status"] == 'cleared' else third_person["status"]
                    else:
                        self.third_person_status = 'pending'
                    self.is_third_person = True
                    super().save(update_fields=['is_third_person', 'third_person_status'])
                ####NEW MATCHING SYSTEM END####

                # current_sender_bank_activites = match_bank_activity_from_iban({
                #     "cross_bank_account_no": self.cross_bank_account_no,
                #     "exclude_pk": self.pk
                # })

                # if current_sender_bank_activites:
                #     print(f"current_sender_bank_activites: {current_sender_bank_activites}")
                #     current_sender_bank_activity_leases = BankActivityLease.objects.select_related().filter(bank_activity__in = current_sender_bank_activites)
                #     distinct_partners = current_sender_bank_activity_leases.values_list("lease__contract__partner_id", flat=True).distinct()

                #     if distinct_partners.count() == 1:
                #         sender_partner_id = distinct_partners.first()
                #         sender_partner = Partner.objects.get(id=sender_partner_id)

                #         contract_numbers = extract_contract_numbers(self.description)
                #         contracts = Contract.objects.select_related().filter(
                #             Q(partner__tc_vkn_no=sender_partner.tc_vkn_no) & Q(code__in=contract_numbers)
                #         )
                        
                #         leases = Lease.objects.select_related("contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation").filter(
                #             (
                #                 Q(contract__partner__tc_vkn_no = sender_partner.tc_vkn_no) |
                #                 Q(contract__quotation_obj__partner__tc_vkn_no = sender_partner.tc_vkn_no) |
                #                 Q(contract__quotation_obj__quick_quotation__partner__tc_vkn_no = sender_partner.tc_vkn_no)
                #             ) &
                #             (
                #                 Q(lease_status = "aktiflestirildi") |
                #                 Q(lease_status = "planlandi") |
                #                 Q(lease_status = "durduruldu")
                #             ) 
                #         ).order_by('contract_id', '-activation_date').distinct('contract_id')
                #     else:
                #         contract_numbers = extract_contract_numbers(self.description)
                #         contracts = Contract.objects.select_related().filter(
                #             Q(partner__tc_vkn_no=self.tc_vkn_no) & Q(code__in=contract_numbers)
                #         )
                        
                #         leases = Lease.objects.select_related("contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation").filter(
                #             (
                #                 Q(contract__partner__tc_vkn_no = self.tc_vkn_no) |
                #                 Q(contract__quotation_obj__partner__tc_vkn_no = self.tc_vkn_no) |
                #                 Q(contract__quotation_obj__quick_quotation__partner__tc_vkn_no = self.tc_vkn_no)
                #             ) &
                #             (
                #                 Q(lease_status = "aktiflestirildi") |
                #                 Q(lease_status = "planlandi") |
                #                 Q(lease_status = "durduruldu")
                #             ) 
                #         ).order_by('contract_id', '-activation_date').distinct('contract_id')
                # else:
                #     contract_numbers = extract_contract_numbers(self.description)
                #     print(f"contract_numbers: {contract_numbers}")
                #     print(f"type of contract_numbers: {type(contract_numbers)}")
                    
                #     contracts = Contract.objects.select_related().filter(
                #         Q(partner__tc_vkn_no=self.tc_vkn_no) & Q(code__in=contract_numbers)
                #     )
                #     print(f"contracts: {contracts}")
                    
                #     leases = Lease.objects.select_related("contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation").filter(
                #         (
                #             Q(contract__partner__tc_vkn_no = self.tc_vkn_no) |
                #             Q(contract__quotation_obj__partner__tc_vkn_no = self.tc_vkn_no) |
                #             Q(contract__quotation_obj__quick_quotation__partner__tc_vkn_no = self.tc_vkn_no)
                #         ) &
                #         (
                #             Q(lease_status = "aktiflestirildi") |
                #             Q(lease_status = "planlandi") |
                #             Q(lease_status = "durduruldu")
                #         ) 
                #     ).order_by('contract_id', '-activation_date').distinct('contract_id')

                #     print(f"leases: {leases}")

                # if leases:
                #     total_processed_amount = Decimal("0.00")
                #     for lease in leases:
                #         bank_activity_lease = BankActivityLease.objects.create(
                #             company = self.company,
                #             bank_activity = self,
                #             lease = lease
                #         )

                #         processed_amount = self.amount

                #         total_overdue_amount = lease.overdue_amount - lease.processed_amount #test
                #         if total_overdue_amount > 0:
                #             #bank_activity_lease.leaseflex_automation = True
                #             if processed_amount > 0:
                #                 if total_overdue_amount <= processed_amount:
                #                     #bank_activity_lease.processed_amount = total_overdue_amount
                #                     processed_amount -= total_overdue_amount
                #                 else:
                #                     #bank_activity_lease.processed_amount = processed_amount
                #                     processed_amount = Decimal("0.00")
                #             # else:
                #             #     bank_activity_lease.leaseflex_automation = False
                #             bank_activity_lease.save()
                #         bank_activity_leases = lease.lease_bank_acitivity_leases.select_related().all()
                #         total_bank_activity_leases_processed_amount = Decimal("0.00")
                #         for item in bank_activity_leases:
                #             total_bank_activity_leases_processed_amount += item.processed_amount
                #         #lease.processed_amount = total_bank_activity_leases_processed_amount
                #         lease.save()
                #         total_processed_amount += total_bank_activity_leases_processed_amount
                #     self.is_reliable_person = True
                #     super().save(update_fields=['is_reliable_person'])

                #     # if total_processed_amount == self.amount:
                #     #     self.is_processed = True
                #     #     self.save()
                # else:
                #     check_third_person_status(self)
                #     super().save(update_fields=['is_reliable_person','is_third_person'])

                # if len(contracts) == 1:
                #     for contract in contracts:
                #         contract_lease = Lease.objects.select_related().filter(
                #             Q(contract=contract) &
                #             (
                #                 Q(lease_status='aktiflestirildi') |
                #                 Q(lease_status='planlandi') |
                #                 Q(lease_status='durduruldu')
                #             )
                #         ).annotate(lease_id_as_int=Cast('lease_id', IntegerField())).order_by("-lease_id_as_int").first()
                #         print(f"contract_lease: {contract_lease}")

                #         bank_activity_lease = BankActivityLease.objects.select_related().filter(bank_activity = self, lease = contract_lease).first()
                #         print(f"bank_activity_lease: {bank_activity_lease}")

                #         if not bank_activity_lease and contract_lease:
                #             bank_activity_lease = BankActivityLease.objects.create(
                #                 company = self.company,
                #                 bank_activity = self,
                #                 lease = contract_lease
                #             )

                #         if bank_activity_lease:
                #             bank_activity_lease.processed_amount = self.amount
                #             bank_activity_lease.leaseflex_automation = True
                #             bank_activity_lease.save()
                #             # first_future_payment = (
                #             #     bank_activity_lease.lease.lease_installments
                #             #     .filter(payment_date__gte=timezone.now().date())
                #             #     .order_by('payment_date')
                #             #     .values_list('amount', flat=True)
                #             #     .first()
                #             # )

                #             # if first_future_payment:
                #             #     if abs(self.amount - first_future_payment) <= 2:
                #             #         bank_activity_lease.processed_amount = self.amount
                #             #         bank_activity_lease.leaseflex_automation = True
                #             #         bank_activity_lease.save()

                # if len(contracts) > 1:
                #     total_contract_ba_leases_ffp_amount = Decimal("0.00")
                #     total_contract_ba_leases_overdue_amount = Decimal("0.00")
                #     total_contract_ba_leases_mix_amount = Decimal("0.00")
                #     contract_ba_lease_queryset = []
                #     for contract in contracts:
                #         contract_lease = Lease.objects.select_related().filter(
                #             Q(contract=contract) &
                #             (
                #                 Q(lease_status='aktiflestirildi') |
                #                 Q(lease_status='planlandi') |
                #                 Q(lease_status='durduruldu')
                #             )
                #         ).annotate(lease_id_as_int=Cast('lease_id', IntegerField())).order_by("-lease_id_as_int").first()

                #         bank_activity_lease = BankActivityLease.objects.select_related().filter(bank_activity = self, lease = contract_lease).first()

                #         if not bank_activity_lease and contract_lease:
                #             bank_activity_lease = BankActivityLease.objects.create(
                #                 company = self.company,
                #                 bank_activity = self,
                #                 lease = contract_lease,
                #                 processed_amount = Decimal("0.00")
                #             )

                #         # if bank_activity_lease:
                #         #     first_future_payment = (
                #         #         bank_activity_lease.lease.lease_installments
                #         #         .filter(payment_date__gte=timezone.now().date())
                #         #         .order_by('payment_date')
                #         #         .values_list('amount', flat=True)
                #         #         .first()
                #         #     )
                #         #     if abs(self.amount == first_future_payment) <= 2:
                #         #         bank_activity_lease.processed_amount = self.amount
                #         #         bank_activity_lease.leaseflex_automation = True
                #         #         bank_activity_lease.save()

                #         if bank_activity_lease:
                #             first_future_payment = (
                #                 bank_activity_lease.lease.lease_installments
                #                 .filter(payment_date__gte=timezone.now().date())
                #                 .order_by('payment_date')
                #                 .values_list('amount', flat=True)
                #                 .first()
                #             )
                #             contract_ba_lease_queryset.append(bank_activity_lease)
                #             total_contract_ba_leases_ffp_amount += first_future_payment
                #             total_contract_ba_leases_overdue_amount += bank_activity_lease.lease.overdue_amount
                #             if total_contract_ba_leases_overdue_amount:
                #                 total_contract_ba_leases_mix_amount += total_contract_ba_leases_overdue_amount
                #             else:
                #                 total_contract_ba_leases_mix_amount += first_future_payment

                #     if abs(self.amount - total_contract_ba_leases_ffp_amount) <= 2:
                #         for contract_ba_lease in contract_ba_lease_queryset:
                #             first_future_payment = (
                #                 contract_ba_lease.lease.lease_installments
                #                 .filter(payment_date__gte=timezone.now().date())
                #                 .order_by('payment_date')
                #                 .values_list('amount', flat=True)
                #                 .first()
                #             )
                #             if first_future_payment:
                #                 contract_ba_lease.processed_amount = first_future_payment
                #                 contract_ba_lease.leaseflex_automation = True
                #                 contract_ba_lease.save()
                #     elif abs(self.amount - total_contract_ba_leases_overdue_amount) <= 2:
                #         for contract_ba_lease in contract_ba_lease_queryset:
                #             lease_overdue_amount = contract_ba_lease.lease.overdue_amount
                #             contract_ba_lease.processed_amount = lease_overdue_amount
                #             contract_ba_lease.leaseflex_automation = True
                #             contract_ba_lease.save()
                #     elif abs(self.amount - total_contract_ba_leases_mix_amount) <= 2:
                #         for contract_ba_lease in contract_ba_lease_queryset:
                #             lease_overdue_amount = contract_ba_lease.lease.overdue_amount
                #             if lease_overdue_amount > 0:
                #                 contract_ba_lease.processed_amount = lease_overdue_amount
                #             else:
                #                 first_future_payment = (
                #                     contract_ba_lease.lease.lease_installments
                #                     .filter(payment_date__gte=timezone.now().date())
                #                     .order_by('payment_date')
                #                     .values_list('amount', flat=True)
                #                     .first()
                #                 )
                #                 contract_ba_lease.processed_amount = first_future_payment
                #             contract_ba_lease.leaseflex_automation = True
                #             contract_ba_lease.save()

                # if len(contracts) == 0 and self.tc_vkn_no:
                #     partner = Partner.objects.select_related().filter(tc_vkn_no = self.tc_vkn_no).first()

                #     if partner:
                #         total_customer_leases_amount = Decimal("0.00")
                #         customer_leases = Lease.objects.select_related().filter(
                #             Q(contract__partner=partner) &
                #             (
                #                 Q(lease_status='aktiflestirildi') |
                #                 Q(lease_status='planlandi') |
                #                 Q(lease_status='durduruldu')
                #             )
                #         ).annotate(lease_id_as_int=Cast('lease_id', IntegerField())).order_by("-lease_id_as_int")

                #         for customer_lease in customer_leases:
                #             first_future_payment = (
                #                 customer_lease.lease_installments
                #                 .filter(payment_date__gte=timezone.now().date())
                #                 .order_by('payment_date')
                #                 .values_list('amount', flat=True)
                #                 .first()
                #             )
                #             if first_future_payment:
                #                 if abs(self.amount - first_future_payment) <= 2:
                #                     pass
                #                 total_customer_leases_amount += first_future_payment
                        
                #         if abs(self.amount - total_customer_leases_amount) <= 2:
                #             for customer_lease in customer_leases:
                #                 bank_activity_lease = BankActivityLease.objects.select_related().filter(bank_activity = self, lease = customer_lease).first()

                #                 if not bank_activity_lease and customer_lease:
                #                     bank_activity_lease = BankActivityLease.objects.create(
                #                         company = self.company,
                #                         bank_activity = self,
                #                         lease = customer_lease
                #                     )

                #             bank_activity_leases = self.bank_activity_bank_acitivity_leases.all()

                #             for bank_activity_lease in bank_activity_leases:
                #                 first_future_payment = (
                #                     bank_activity_lease.lease.lease_installments
                #                     .filter(payment_date__gte=timezone.now().date())
                #                     .order_by('payment_date')
                #                     .values_list('amount', flat=True)
                #                     .first()
                #                 )
                #                 if first_future_payment:
                #                     bank_activity_lease.processed_amount = first_future_payment
                #                     bank_activity_lease.leaseflex_automation = True
                #                     bank_activity_lease.save()
                        
                #             if self.amount != total_customer_leases_amount and bank_activity_leases:
                #                 diff_amount = self.amount - total_customer_leases_amount

                #                 last_bank_activity_lease = bank_activity_leases.last()
                #                 last_bank_activity_lease.processed_amount += diff_amount
                #                 last_bank_activity_lease.save()
                                    


            # self.created_date = datetime.now() - timedelta(days=1)
            # super().save(update_fields=['created_date'])

            ba_leases = self.bank_activity_bank_acitivity_leases.filter(leaseflex_automation = True)
            if ba_leases:
                total_ba_leases_amount = Decimal("0.00")
                for ba_lease in ba_leases:
                    total_ba_leases_amount += ba_lease.processed_amount

                if self.amount == total_ba_leases_amount:
                    self.is_processed = True
                    super().save(update_fields=['is_processed'])
                else:
                    self.is_processed = False
                    super().save(update_fields=['is_processed'])
          
    
class BankActivityLease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="bank_activity_leases")

    bank_activity = models.ForeignKey(BankActivity, on_delete=models.CASCADE, related_name="bank_activity_bank_acitivity_leases")
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_bank_acitivity_leases")
    processed_amount = models.DecimalField(_("Processed Amount"), default = Decimal("0.00"), max_digits=14, decimal_places=2,null = True, blank = True)
    leaseflex_automation = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.bank_activity.tc_vkn_no)
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            super().save(*args, **kwargs)
            
            if not is_new:
                ba_leases = BankActivityLease.objects.filter(bank_activity = self.bank_activity, leaseflex_automation = True)
                total_ba_leases_amount = 0
                for ba_lease in ba_leases:
                    total_ba_leases_amount += ba_lease.processed_amount

                if self.bank_activity.amount == total_ba_leases_amount:
                    BankActivity.objects.filter(pk=self.bank_activity.pk).update(is_processed=True)
                else:
                    BankActivity.objects.filter(pk=self.bank_activity.pk).update(is_processed=False)
    
class PartnerOverdueView(models.Model):
    partner = models.OneToOneField(Partner, on_delete=models.DO_NOTHING, primary_key=True, db_column='partner_id')
    max_overdue_days = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partner_max_overdue_days'

