from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from common.models import Status,Currency
from companies.models import Company

# Create your models here.



class BlackListPerson(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="black_list_persons")

    name = models.CharField(_("Name"), max_length=250, null=True, blank=True)
    tc_vkn_passport_no = models.CharField(_("TC/VKN/Passport No"), max_length=500, null=True, blank=True)
    other_names = models.CharField(_("Other Names"), max_length=1250, null=True, blank=True)
    nationality = models.CharField(_("Nationality"), max_length=140, null=True, blank=True)
    birthday = models.CharField(_("Birthday"), max_length=140, null=True, blank=True)
    organization = models.CharField(_("Organization"), max_length=250, null=True, blank=True)
    date_number = models.CharField(_("Date/Number"), max_length=50, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.uuid)