from django.db import models, transaction
from django.db.models import Q,IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re
from itertools import chain
from datetime import datetime,timedelta
import requests
from requests.auth import HTTPBasicAuth
import ollama

from underwriting.utils import check_third_person_status
from companies.models import Company
from common.models import Currency, Status
from common.utils.ai_utils import EXAMPLE_DEF,EXAMPLE_LIST
from contracts.models import Contract
from partners.models import Partner
from finance.models import FinmaksTransaction
from compliance.utils.third_person_utils import create_third_person
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
    lease_status_update_date = models.DateTimeField(_("Lease Status Update Date"), blank=True, null=True)
    
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_leases")
    musteri_baz_maliyet = models.DecimalField(_("Müşteri Baz Maliyet"), default = 0.00, max_digits=14, decimal_places=2)
    vade = models.IntegerField(_("Vade"), default = 0)
    leasing_rate = models.DecimalField(_("Leasing Rate"), default = 0.00, max_digits=14, decimal_places=2)
    irr = models.DecimalField(_("IRR"), default = 0.00, max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(_("Interest Rate"), default = 0.00, max_digits=14, decimal_places=2)
    total_payment = models.DecimalField(_("Total Payment"), default = 0.00, max_digits=14, decimal_places=2)
    paid = models.DecimalField(_("Paid"), default = 0.00, max_digits=14, decimal_places=2)
    paid_rate = models.DecimalField(_("Paid Rate"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_amount = models.DecimalField(_("Overdue Amount"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_days = models.IntegerField(_("Overdue Days"), default=0)
    overdue_0_30 = models.DecimalField(_("Overdue 0 - 30"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_31_60 = models.DecimalField(_("Overdue 31 - 60"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_61_90 = models.DecimalField(_("Overdue 61 - 90"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_91_120 = models.DecimalField(_("Overdue 91 - 120"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_121_150 = models.DecimalField(_("Overdue 121 - 150"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_151_180 = models.DecimalField(_("Overdue 151 - 180"), default = 0.00, max_digits=14, decimal_places=2)
    overdue_181_gte = models.DecimalField(_("Overdue 181 >"), default = 0.00, max_digits=14, decimal_places=2)
    first_installment_date = models.DateField(_("First Installment Date"), blank=True, null=True)

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
    is_processed = models.BooleanField(default=False)

    is_kdv_diff = models.BooleanField(default=False)
    is_agreed_terminated = models.BooleanField(default=False)
    is_credit = models.BooleanField(default=False)
    is_under_review = models.BooleanField(default=False)

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
    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    interest = models.DecimalField(_("Interest"), default = 0.00, max_digits=14, decimal_places=2)
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
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_bank_activities")
    receipt_no = models.CharField(_("Receipt No"), max_length=140, blank=True, null=True)
    description = models.CharField(_("Description"), max_length=500, blank=True, null=True)
    name = models.CharField(_("Name"), max_length=500, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)

    leases = models.ManyToManyField(Lease,related_name='lease_bank_activities', blank = True)

    is_certain = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    is_third_person = models.BooleanField(default=False)
    is_reliable_person = models.BooleanField(default=False)
    THIRD_PERSON_STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('cleared', ('Cleared')),
        ('flagged', ('Flagged')),
    )
    third_person_status = models.CharField(_("Third Person Status"), max_length=25, default='pending', choices=THIRD_PERSON_STATUS_CHOICES, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
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
                    create_third_person(self,scan_result)
                    if scan_result == 'cleared':
                        self.third_person_status = scan_result
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
    processed_amount = models.DecimalField(_("Processed Amount"), default = 0.00, max_digits=14, decimal_places=2,null = True, blank = True)
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

