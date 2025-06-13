from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City

# Create your models here.

class BankaHareketi(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="banka_hareketleri")

    gonderen_unvani = models.CharField(_("Gönderen Ünvanı"), max_length=250)
    musteri_unvani = models.CharField(_("Müşteri Ünvanı"), max_length=250)
    aciklama = models.CharField(_("Açıklama"), max_length=250)
    ucuncu_sahis_mi = models.BooleanField(default=False)
    ucuncu_sahis_mi_str = models.CharField(_("Üçüncü Şahıs"), max_length=25, default="")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.gonderen_unvani)

class BankaTahsilati(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="banka_tahsilatlari")

    gonderen_unvani = models.CharField(_("Gönderen Ünvanı"), max_length=250)
    tc_vkn_no = models.CharField(_("TC/VKN NO"), max_length=140)
    aciklama = models.CharField(_("Açıklama"), max_length=250)
    tutar = models.DecimalField(_("Tutar"), default = 0.00, max_digits=14, decimal_places=2)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.gonderen_unvani)

class BankaTahsilatiOdoo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="banka_tahsilatlari_odoo")

    gonderen_unvani = models.CharField(_("Gönderen Ünvanı"), max_length=250)
    tc_vkn_no = models.CharField(_("TC/VKN NO"), max_length=140)
    aciklama = models.CharField(_("Açıklama"), max_length=250)
    tutar = models.DecimalField(_("Tutar"), default = 0.00, max_digits=14, decimal_places=2)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.gonderen_unvani)