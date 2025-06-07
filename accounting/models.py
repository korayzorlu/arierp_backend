from django.db import models,transaction

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal

from .utils import get_or_create_account,create_transaction

from partners.models import Partner
from common.models import Currency
from companies.models import Company

# Create your models here.

class AccountCategory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    code = models.CharField(_("Code"), max_length=50, blank = True, null=True)
    name = models.CharField(_("Name"), max_length=50, blank = True, null=True)

    def __str__(self):
        return str(self.name)

class AccountType(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name="types")
    code = models.CharField(_("Code"), max_length=50, blank = True, null=True)
    name = models.CharField(_("Name"), max_length=50, blank = True, null=True)

    def __str__(self):
        return str(self.name)

class Account(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="accounts")

    type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name="account_type_accounts")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True, related_name="partner_accounts")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_accounts")

    balance = models.DecimalField(_("Balance"), default = 0.00, max_digits=14, decimal_places=2)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['partner', 'currency'], name='unique_partner_currency')
        ]

    def __str__(self):
        return str(f"{self.type.category} - {self.type} - {self.currency.code}")
    
class Transaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="transactions")

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="account_transactions")

    ref_uuid = models.CharField(_("Ref UUID"), max_length=140)

    TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit')
    ]
    type = models.CharField(_("Type"), max_length=10, choices=TYPES, default = "debit")
    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    date = models.DateTimeField(_("Date"), auto_now_add=True, null=True)

    description = models.TextField(_("Description"), blank = True, null = True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.account.partner.name} -  {self.type} - {self.amount}")
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            if not is_new:
                # Önce eski veriyi al
                old = Transaction.objects.get(pk=self.pk)
                self._reverse_balance(old)

            # Yeni değeri uygula
            self._apply_balance()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self._reverse_balance(self)
            super().delete(*args, **kwargs)

    def _apply_balance(self):
        self.account.balance = Decimal(self.account.balance)
        if self.account.type.code == 'receivable':
            if self.type == 'debit':
                self.account.balance += self.amount  # Alacak arttı
            elif self.type == 'credit':
                self.account.balance -= self.amount  # Tahsilat yapıldı

        elif self.account.type.code == 'payable':
            if self.type == 'debit':
                self.account.balance -= self.amount  # Borç ödendi
            elif self.type == 'credit':
                self.account.balance += self.amount  # Borç oluştu

        if self.account.type.code == 'capital':
            if self.type == 'debit':
                self.account.balance += self.amount
            elif self.type == 'credit':
                self.account.balance -= self.amount

        elif self.account.type.code == 'sales':
            if self.type == 'debit':
                self.account.balance -= self.amount
            elif self.type == 'credit':
                self.account.balance += self.amount

        elif self.account.type.code == 'expense':
            if self.type == 'debit':
                self.account.balance += self.amount
            elif self.type == 'credit':
                self.account.balance -= self.amount

        elif self.account.type.code == 'bank':
            if self.type == 'debit':
                self.account.balance += self.amount
            elif self.type == 'credit':
                self.account.balance -= self.amount

        elif self.account.type.code == 'cash':
            if self.type == 'debit':
                self.account.balance += self.amount
            elif self.type == 'credit':
                self.account.balance -= self.amount

        self.account.save()

    def _reverse_balance(self, txn):
        self.account.balance = Decimal(self.account.balance)
        if txn.account.type.code == 'receivable':
            if txn.type == 'debit':
                self.account.balance -= txn.amount  # Önceki etkisini tersine al
            elif txn.type == 'credit':
                self.account.balance += txn.amount

        elif txn.account.type.code == 'payable':
            if txn.type == 'debit':
                self.account.balance += txn.amount
            elif txn.type == 'credit':
                self.account.balance -= txn.amount 

        if txn.account.type.code == 'capital':
            if txn.type == 'debit':
                self.account.balance -= txn.amount
            elif txn.type == 'credit':
                self.account.balance += txn.amount

        elif txn.account.type.code == 'sales':
            if txn.type == 'debit':
                self.account.balance += txn.amount
            elif txn.type == 'credit':
                self.account.balance -= txn.amount

        elif txn.account.type.code == 'expense':
            if txn.type == 'debit':
                self.account.balance -= txn.amount
            elif txn.type == 'credit':
                self.account.balance += txn.amount

        elif txn.account.type.code == 'bank':
            if txn.type == 'debit':
                self.account.balance -= txn.amount
            elif txn.type == 'credit':
                self.account.balance += txn.amount

        elif txn.account.type.code == 'cash':
            if txn.type == 'debit':
                self.account.balance -= txn.amount
            elif txn.type == 'credit':
                self.account.balance += txn.amount

        self.account.save()

class Invoice(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="invoices")

    invoice_no = models.CharField(_("Invoice No"), max_length=140, blank = True, null=True)

    TYPES = [
        ('sale', 'Sales Invoice'),
        ('purchase', 'Purchase Invoice'),
    ]
    type = models.CharField(_("Type"), max_length=10, choices=TYPES, default = "sale")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_invoices")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_invoices")

    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    date = models.DateTimeField(_("Date"), auto_now_add=True, null=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.partner.name} - {self.invoice_no}")
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            if is_new:
                self._get_or_create_acc_txn()
            else:
                txns = Transaction.objects.filter(ref_uuid = str(self.uuid))
                old_invoice = Invoice.objects.get(pk=self.pk)

                partner_changed = self.partner != old_invoice.partner
                currency_changed = self.currency != old_invoice.currency

                if partner_changed or currency_changed:
                    # Eski Transaction'ın etkisini kaldır
                    for txn in txns:
                        txn.delete()

                    self._get_or_create_acc_txn()

                else:
                    for txn in txns:
                        txn.amount = self.amount
                        txn.save()

            super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        with transaction.atomic():
            txns = Transaction.objects.filter(ref_uuid = str(self.uuid))
            for txn in txns:
                txn.delete()
            super().delete(*args, **kwargs)

    def _get_or_create_acc_txn(self):
        description = f"{self.get_type_display()} - {self.invoice_no or ''}"
        if self.type == 'sale':
            receivable_account = get_or_create_account(self.company, self.currency, "receivable", self.partner)
            sales_account = get_or_create_account(self.company, self.currency, "sales")
            receivable_txn = create_transaction(self.company, "debit", receivable_account, self.amount, self.uuid,description)
            sales_txn = create_transaction(self.company, "credit", sales_account, self.amount, self.uuid,description)
        elif self.type == 'purchase':
            payable_account = get_or_create_account(self.company, self.currency, "payable", self.partner)
            expense_account = get_or_create_account(self.company, self.currency, "expense")
            payable_txn = create_transaction(self.company, "credit", payable_account, self.amount, self.uuid,description)
            expense_txn = create_transaction(self.company, "debit", expense_account, self.amount, self.uuid,description)

class Payment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="payments")

    payment_no = models.CharField(_("Payment No"), max_length=140, blank = True, null=True)

    TYPES = [
        ('incoming', 'Incoming Payment'),
        ('outgoing', 'Outgoing Payment'),
    ]
    type = models.CharField(_("Type"), max_length=10, choices=TYPES, default = "incoming")

    RECEIVERS = [
        ('bank', 'Bank'),
        ('cash', 'Cash'),
    ]
    receiver = models.CharField(_("Receiver"), max_length=10, choices=RECEIVERS, default = "bank")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_payments")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_payments")

    amount = models.DecimalField(_("Amount"), default = 0.00, max_digits=14, decimal_places=2)
    date = models.DateTimeField(_("Date"), auto_now_add=True, null=True)

    description = models.TextField(_("Description"), blank = True, null = True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.partner.name} - {self.invoice_no}")
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self._state.adding

            if is_new:
                self._get_or_create_acc_txn()
            else:
                txns = Transaction.objects.filter(ref_uuid = str(self.uuid))
                old_payment = Payment.objects.get(pk=self.pk)

                partner_changed = self.partner != old_payment.partner
                currency_changed = self.currency != old_payment.currency
                receiver_changed = self.receiver != old_payment.receiver

                if partner_changed or currency_changed or receiver_changed:
                    # Eski Transaction'ın etkisini kaldır
                    for txn in txns:
                        txn.delete()

                    self._get_or_create_acc_txn()
                else:
                    for txn in txns:
                        txn.amount = self.amount
                        txn.save()

            super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        with transaction.atomic():
            txns = Transaction.objects.filter(ref_uuid = str(self.uuid))
            for txn in txns:
                txn.delete()
            super().delete(*args, **kwargs)

    def _get_or_create_acc_txn(self):
        if "shareholder" in self.partner.types:
            description = f"{'Capital Injection' if self.type == 'incoming' else 'Capital Withdrawal'} - {self.payment_no or ''}{f' - {self.partner.name}' if self.partner else ''}"
        else:
            description = f"Payment - {self.payment_no or ''}{f' - {self.partner.name}' if self.partner else ''}"
        if self.type == 'incoming':
            receivable_account = get_or_create_account(self.company, self.currency, "capital" if "shareholder" in self.partner.types else "receivable", self.partner)
            bank_account = get_or_create_account(self.company, self.currency, "bank" if self.receiver == "bank" else "cash")
            receivable_txn = create_transaction(self.company, "credit", receivable_account, self.amount, self.uuid,description)
            bank_txn = create_transaction(self.company, "debit", bank_account, self.amount, self.uuid,description)
        elif self.type == 'outgoing':
            payable_account = get_or_create_account(self.company, self.currency, "capital" if "shareholder" in self.partner.types else "payable", self.partner)
            bank_account = get_or_create_account(self.company, self.currency, "bank" if self.receiver == "bank" else "cash")
            payable_txn = create_transaction(self.company, "debit", payable_account, self.amount, self.uuid,description)
            bank_txn = create_transaction(self.company, "credit", bank_account, self.amount, self.uuid,description)