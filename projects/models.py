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