from django.db import models
from django.conf import settings

from django.utils.translation import gettext_lazy as _

from companies.models import Company

import uuid

# Create your models here.

class TimestampModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ImportProcess(TimestampModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="import_processes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_import_processes")
    model_name = models.CharField(_("Model Name"), max_length=140)
    task_id = models.CharField(_("Task ID"), max_length=250, unique=True)
    STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('in_progress', ('In Progress')),
        ('completed', ('Completed')),
        ('rejected', ('Rejected'))
    )
    status = models.CharField(_("Status"), max_length=25, default='pending', choices=STATUS_CHOICES, blank=True, null=True)
    progress = models.PositiveIntegerField(_("Progress"), default=0)
    items_count = models.PositiveIntegerField(_("Items Count"), default=0)

    def __str__(self):
        return str(f"{self.model_name} - {self.user.get_full_name()}")
    
class ExportProcess(TimestampModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="export_processes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_export_processes")
    model_name = models.CharField(_("Model Name"), max_length=140)
    file_name = models.CharField(_("File Name"), max_length=250,null=True,blank=True)
    export_url = models.CharField(_("Export Url"), max_length=250,null=True,blank=True)
    task_id = models.CharField(_("Task ID"), max_length=250, unique=True)
    STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('in_progress', ('In Progress')),
        ('completed', ('Completed')),
        ('rejected', ('Rejected'))
    )
    status = models.CharField(_("Status"), max_length=25, default='pending', choices=STATUS_CHOICES, blank=True, null=True)
    progress = models.PositiveIntegerField(_("Progress"), default=0)
    items_count = models.PositiveIntegerField(_("Items Count"), default=0)

    def __str__(self):
        return str(f"{self.model_name} - {self.user.get_full_name()}")
    
class Country(models.Model):
    name = models.CharField(_("Name"), max_length=150, blank=True, null=True)
    formal_name = models.CharField(_("Formal Name"), max_length=150, blank=True, null=True)
    iso2 = models.CharField(_("iso2"), max_length=15, blank=True, null=True)
    iso3 = models.CharField(_("iso3"), max_length=15, blank=True, null=True)
    dial_code = models.CharField(_("Dial Code"), max_length=15, blank=True, null=True)
    emoji = models.CharField(_("Emoji"), max_length=15, blank=True, null=True)
    flag = models.CharField(_("Flag"), max_length=150, blank=True, null=True)
    #afg old flag: https://flagcdn.com/af.svg
    
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_cities")
    name = models.CharField(_("City"), max_length=150, null=True, blank=True, db_index=True)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.name)

class Currency(models.Model):
    countries = models.ManyToManyField(Country,related_name='country_currencies', blank = True)
    code = models.CharField(_("Code"), max_length=25, null=True, blank=True)
    name = models.CharField(_("Name"), max_length=50, null=True, blank=True)
    symbol = models.CharField(_("Symbol"), max_length=25, null=True, blank=True)
    exchange_rate = models.DecimalField(_("Exchange Rate"), default = 0.00, max_digits=10, decimal_places=4)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.code)
    
class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="base_currency_exchange_rates", null=True, blank=True)
    target_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="target_currency_exchange_rates", null=True, blank=True)

    date = models.DateField(_("Date"), blank=True, null=True)
    forex_buying = models.DecimalField(_("Forex Buying"), default = 0.00, max_digits=14, decimal_places=2)
    forex_selling = models.DecimalField(_("Forex Selling"), default = 0.00, max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(f"{self.base_currency.code} - {self.target_currency.code} - {self.date}")
    
class TufeRate(models.Model):
    code = models.CharField(_("Code"), max_length=25, null=True, blank=True)
    date = models.DateField(_("Date"), blank=True, null=True)
    rate = models.DecimalField(_("Rate"), default = 0.00, max_digits=14, decimal_places=2)
    change_rate = models.DecimalField(_("Change Rate"), default = 0.00, max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(f"{self.rate} - {self.change_rate} - {self.date}")

class MainStatus(models.Model):
    name = models.CharField(_("Name"), max_length=25)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.name)

class Status(models.Model):
    MODEL_CHOICES = (
        ('contract', ('Contract')),
        ('credit', ('Credit')),
        ('invoice', ('Invoice')),
        ('incoming_request', ('Incoming Request')),
        ('insurance_policy', ('Insurance Policy')),
        ('lease_purchase_document', ('Lease Purchase Document')),
        ('lease_purchase_order', ('Lease Purchase Order')),
        ('lease_purchase_project', ('Lease Purchase Project')),
        ('lease_operation_project', ('Lease Operation Project')),
        ('op_leasing', ('Op Leasing')),
        ('quotation', ('Quotation')),
        ('rpr_quo', ('RPR QUO')),
        ('trade_guarantee', ('Trade Guarantee'))
    )
    model = models.CharField(_("Model"), max_length=25, default='contract', choices=MODEL_CHOICES, blank=True, null=True)

    main_status = models.ForeignKey(MainStatus, on_delete=models.SET_NULL, blank=True, null=True, related_name="main_status_statusses")

    name = models.CharField(_("Name"), max_length=140)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.name)