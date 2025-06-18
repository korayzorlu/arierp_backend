from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Currency, Status
from contracts.models import Contract

# Create your models here.

class Lease(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="rents")

    code = models.CharField(_("Code"), max_length=25)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="pcontract_rents")
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

    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name="currency_rents")
    musteri_baz_maliyet = models.DecimalField(_("Müşteri Baz Maliyet"), default = 0.00, max_digits=14, decimal_places=2)
    vade = models.IntegerField(_("Vade"), default = 0)
    leasing_rate = models.DecimalField(_("Leasing Rate"), default = 0.00, max_digits=8, decimal_places=2)
    irr = models.DecimalField(_("IRR"), default = 0.00, max_digits=14, decimal_places=2)

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

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
