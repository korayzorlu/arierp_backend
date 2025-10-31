from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Currency, Status
from partners.models import Partner

# Create your models here.
class Project(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")

    project_id = models.CharField(_("Project ID"), max_length=25, null=True, blank=True)
    name = models.CharField(_("Name"), max_length=500, null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_projects", null=True, blank=True)
    comission_rate = models.DecimalField(_("Comission Rate"), default = 0.00, max_digits=14, decimal_places=2)
    term_diff_rate = models.DecimalField(_("Term Diff Rate"), default = 0.00, max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
class Parcel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="parcels")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_parcels", null=True, blank=True)
    parcel_id = models.CharField(_("Parcel ID"), max_length=25, null=True, blank=True)
    no = models.CharField(_("No"), max_length=25, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.no}"
    
class RealEstate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="real_estates")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_real_estates", null=True, blank=True)
    real_estate_id = models.CharField(_("Real Estate ID"), max_length=25, null=True, blank=True)
    parcel = models.CharField(_("Parcel"), max_length=25, null=True, blank=True)
    block = models.CharField(_("Block"), max_length=25, null=True, blank=True)
    unit = models.CharField(_("Unit"), max_length=25, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.block} - {self.unit}"
    
class TitleDeed(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="title_deads")

    tasinmaz_no = models.CharField(_("Taşınmaz No"), max_length=25, null=True, blank=True)
    nitelik = models.CharField(_("Nitelik"), max_length=50, null=True, blank=True)
    il = models.CharField(_("İl"), max_length=25, null=True, blank=True)
    ilce = models.CharField(_("İlçe"), max_length=50, null=True, blank=True)
    mahalle = models.CharField(_("Mahalle"), max_length=50, null=True, blank=True)
    yuzolcum = models.DecimalField(_("Yüzölçüm"), default=0.00, max_digits=14, decimal_places=2)
    ada = models.CharField(_("Ada"), max_length=25, null=True, blank=True)
    parsel = models.CharField(_("Parsel"), max_length=25, null=True, blank=True)
    unit = models.CharField(_("Unit"), max_length=25, null=True, blank=True)
    zemin_hisse_id = models.CharField(_("Zemin Hisse ID"), max_length=50, null=True, blank=True)
    zemin_tipi = models.CharField(_("Zemin Tipi"), max_length=50, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tasinmaz_no} - {self.nitelik}"