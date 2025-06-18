from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from common.models import Status
from companies.models import Company
from partners.models import Partner

# Create your models here.



class Contract(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="contracts")

    code = models.CharField(_("Code"), max_length=25)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_contracts", null=True, blank=True)
    kof = models.CharField(_("Kof"), max_length=25, null=True, blank=True)
    quotation = models.CharField(_("Quotation"), max_length=25, null=True, blank=True)
    committe = models.CharField(_("Committe"), max_length=25, null=True, blank=True)
    credit_type = models.CharField(_("Credit Type"), max_length=25, null=True, blank=True)
    customer_representative = models.CharField(_("Customer Representative"), max_length=140, null=True, blank=True)
    supplier = models.CharField(_("Supplier"), max_length=140, null=True, blank=True)
    project = models.CharField(_("Project"), max_length=250, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, related_name="status_contracts", null=True, blank=True)
    mkk_tesciline_gonderilecek_mi = models.BooleanField(default=False)
    kof_tan_sozlesmeye_aktarim_tarihi = models.DateTimeField(_("Kof'tan Sözleşmeye Aktarım Tarihi"), blank=True, null=True)
    lop_open_date = models.DateTimeField(_("Lop Open Date"), blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.code)
    
