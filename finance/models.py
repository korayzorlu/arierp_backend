from django.db import models, transaction
from django.db.models import Q,IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re
from itertools import chain
from datetime import datetime,timedelta
import requests
from requests.auth import HTTPBasicAuth

from companies.models import Company
from common.models import Currency

# Create your models here.

class FinmaksBankAccount(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="finmaks_bank_accounts")

    bank_account_id = models.CharField(_("Bank Account Id"), max_length=25, null=True, blank=True)
    iban = models.CharField(_("IBAN"), max_length=50, null=True, blank=True)
    account_no = models.CharField(_("Account No"), max_length=25, null=True, blank=True)
    branch_code = models.CharField(_("Branch Code"), max_length=140, null=True, blank=True)
    branch_name = models.CharField(_("Branch Name"), max_length=250, null=True, blank=True)
    finmaks_account_type = models.CharField(_("Finmaks Account Type"), max_length=25, null=True, blank=True)

    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    available_balance = models.DecimalField(_("Available Balance"), default = 0.00, max_digits=14, decimal_places=2)
    over_draft = models.DecimalField(_("Over Draft"), default = 0.00, max_digits=14, decimal_places=2)
    credit_risk = models.DecimalField(_("Credit Risk"), default = 0.00, max_digits=14, decimal_places=2)
    blocked_balance = models.DecimalField(_("Blocked Balance"), default = 0.00, max_digits=14, decimal_places=2)
    credit_limit = models.DecimalField(_("Credit Limit"), default = 0.00, max_digits=14, decimal_places=2)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_bank_accounts")
    currency_type = models.CharField(_("Currency Type"), max_length=25, null=True, blank=True)
    bank_name = models.CharField(_("Bank Name"), max_length=25, null=True, blank=True)
    bank_code = models.CharField(_("Bank Code"), max_length=25, null=True, blank=True)
    bank_integration_info_id = models.CharField(_("Bank Integration Info Id"), max_length=25, null=True, blank=True)

    last_read_time = models.DateTimeField(_("Last Read Time"), blank=True, null=True)
    status = models.BooleanField(default=False)

    finekra_bank_account_id = models.CharField(_("Finekra Bank Account Id"), max_length=250, null=True, blank=True)
    
    is_active = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.bank_name)
    
class FinmaksBankAccountDailyRecord(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="finmaks_bank_account_daily_records")

    finmaks_bank_account = models.ForeignKey(FinmaksBankAccount, on_delete=models.CASCADE, related_name="finmaks_bank_account_finmaks_bank_account_daily_records")
    date = models.DateField(_("Date"), blank=True, null=True)

    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    available_balance = models.DecimalField(_("Available Balance"), default = 0.00, max_digits=14, decimal_places=2)
    over_draft = models.DecimalField(_("Over Draft"), default = 0.00, max_digits=14, decimal_places=2)
    credit_risk = models.DecimalField(_("Credit Risk"), default = 0.00, max_digits=14, decimal_places=2)
    blocked_balance = models.DecimalField(_("Blocked Balance"), default = 0.00, max_digits=14, decimal_places=2)
    credit_limit = models.DecimalField(_("Credit Limit"), default = 0.00, max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.finmaks_bank_account.bank_name)
    
class FinmaksTransaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="finmaks_transactions")

    bank_account = models.ForeignKey(FinmaksBankAccount, on_delete=models.CASCADE, related_name="finmaks_bank_account_finmaks_transactions", null=True, blank=True)

    transaction_id = models.CharField(_("Transaction Id"), max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(_("Transaction Date"), blank=True, null=True)
    explanation_field = models.CharField(_("Explanation Field"), max_length=500, null=True, blank=True)
    description = models.CharField(_("Description"), max_length=500, null=True, blank=True)
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    sender_vkn = models.CharField(_("Sender VKN"), max_length=50, null=True, blank=True)
    sender_iban = models.CharField(_("Sender IBAN"), max_length=50, null=True, blank=True)
    sender_account_name = models.CharField(_("SenderAccountName"), max_length=250, null=True, blank=True)
    receiver_vkn = models.CharField(_("Receiver VKN"), max_length=50, null=True, blank=True)
    receiver_iban = models.CharField(_("Receiver IBAN"), max_length=50, null=True, blank=True)
    receipt_number = models.CharField(_("Receipt Number"), max_length=50, null=True, blank=True)
    value_date = models.DateTimeField(_("Value Date"), blank=True, null=True)
    transaction_type = models.CharField(_("Transaction Type"), max_length=50, null=True, blank=True)
    bank_code = models.CharField(_("Bank Code"), max_length=50, null=True, blank=True)
    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    firm_id = models.CharField(_("Firm Id"), max_length=50, null=True, blank=True)
    firm_name = models.CharField(_("Firm Name"), max_length=50, null=True, blank=True)
    firm_merchantId = models.CharField(_("Firm Merchant Id"), max_length=50, null=True, blank=True)
    firm_externalCode = models.CharField(_("Firm External Code"), max_length=50, null=True, blank=True)
    firm_externalId = models.CharField(_("Firm ExternalId"), max_length=50, null=True, blank=True)
    transaction_branch_code = models.CharField(_("Transaction Branch Code"), max_length=50, null=True, blank=True)
    transaction_branch_name = models.CharField(_("Transaction Branch Name"), max_length=50, null=True, blank=True)
    firm_code = models.CharField(_("Firm Code"), max_length=50, null=True, blank=True)
    currency_type = models.CharField(_("Currency Type"), max_length=50, null=True, blank=True)
    debit = models.CharField(_("Debit"), max_length=50, null=True, blank=True)
    branch_code = models.CharField(_("Branch Code"), max_length=50, null=True, blank=True)
    transaction_external_id = models.CharField(_("Transaction External Id"), max_length=50, null=True, blank=True)
    external_id_used = models.BooleanField(default=False)
    external_bank_id = models.CharField(_("External Bank Id"), max_length=50, null=True, blank=True)
    reference_no = models.CharField(_("Reference No"), max_length=50, null=True, blank=True)
    finmaks_process_type = models.CharField(_("Finmaks Process Type"), max_length=50, null=True, blank=True)
    category_name = models.CharField(_("Category Name"), max_length=50, null=True, blank=True)
    integration_field_value = models.CharField(_("Category Name"), max_length=50, null=True, blank=True)
    transaction_status = models.CharField(_("Transaction Status"), max_length=50, null=True, blank=True)

    is_vpos = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.transaction_id)
    
class VPosTransaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vpos_transactions")

    process_date = models.DateTimeField(_("Process Date"), blank=True, null=True)
    musteri_tipi = models.PositiveIntegerField(_("Customer Type"), default=0)

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_vpos_transactions")
    paid_amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)

    lease_posting_group_id = models.BooleanField(default=False)

    firma_adi = models.CharField(_("Firma Adı"), max_length=250, null=True, blank=True)
    kurum_tipi = models.CharField(_("Kurum Tipi"), max_length=50, null=True, blank=True)
    vergi_dairesi = models.CharField(_("Vergi Dairesi"), max_length=140, null=True, blank=True)
    vergi_no = models.CharField(_("Vergi No"), max_length=50, null=True, blank=True)
    web_sitesi = models.CharField(_("Web Sitesi"), max_length=250, null=True, blank=True)
    adres = models.CharField(_("Adres"), max_length=250, null=True, blank=True)
    ulke = models.CharField(_("Ülke"), max_length=140, null=True, blank=True)
    sehir = models.CharField(_("Şehir"), max_length=50, null=True, blank=True)
    ilce = models.CharField(_("İlçe"), max_length=50, null=True, blank=True)
    posta = models.CharField(_("Posta"), max_length=50, null=True, blank=True)

    ad = models.CharField(_("Ad"), max_length=140, null=True, blank=True)
    ikinci_ad = models.CharField(_("İkinci Ad"), max_length=140, null=True, blank=True)
    orta_ad = models.CharField(_("Orta Ad"), max_length=140, null=True, blank=True)
    soyad = models.CharField(_("Soyad"), max_length=140, null=True, blank=True)
    cinsiyet = models.CharField(_("Cinsiyet"), max_length=50, null=True, blank=True)
    tc_kimlik_no = models.CharField(_("TC Kimlik No"), max_length=25, null=True, blank=True)
    pasaport_no = models.CharField(_("Pasaport No"), max_length=25, null=True, blank=True)
    uyruk = models.CharField(_("Uyruk"), max_length=50, null=True, blank=True)
    dogum_tarihi = models.CharField(_("Doğum Tarihi"), max_length=50, null=True, blank=True)
    vergi_dairesi_birey = models.CharField(_("Vergi Dairesi Birey"), max_length=140, null=True, blank=True)
    vergi_no_birey = models.CharField(_("Vergi No Birey"), max_length=50, null=True, blank=True)
    adres_birey = models.CharField(_("Adres Birey"), max_length=250, null=True, blank=True)
    ulke_birey = models.CharField(_("Ülke Birey"), max_length=140, null=True, blank=True)
    sehir_birey = models.CharField(_("Şehir Birey"), max_length=50, null=True, blank=True)
    ilce_birey = models.CharField(_("İlçe Birey"), max_length=50, null=True, blank=True)
    posta_birey = models.CharField(_("Posta Birey"), max_length=50, null=True, blank=True)
    
    username = models.CharField(_("User Name"), max_length=140, null=True, blank=True)
    password = models.CharField(_("Password"), max_length=140, null=True, blank=True)
    telefon = models.CharField(_("Telefon"), max_length=50, null=True, blank=True)
    email = models.CharField(_("Email"), max_length=140, null=True, blank=True)
    fax = models.CharField(_("Fax"), max_length=50, null=True, blank=True)
    bank_code = models.CharField(_("Bank Code"), max_length=25, null=True, blank=True)
    contract_code = models.CharField(_("Contract Code"), max_length=25, null=True, blank=True)
    ext_transaction_id = models.CharField(_("External Transaction ID"), max_length=140, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company.name} - {self.paid_amount} {self.currency}"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
class VPosIletisim(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vpos_iletisims")

    vpos_transaction = models.ForeignKey(VPosTransaction, on_delete=models.CASCADE, related_name="vpos_transaction_vpos_iletisims")
    iletisim_turu = models.CharField(max_length=50, null=True, blank=True)
    iletisim_degeri = models.CharField(max_length=250, null=True, blank=True)
    TYPE_CHOICES = (
        ('bireysel', ('Bireysel')),
        ('kurumsal', ('Kurumsal')),
    )
    type = models.CharField(_("Type"), max_length=25, default='bireysel', choices=TYPE_CHOICES, blank=True, null=True)