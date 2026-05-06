from django.db import models, transaction
from django.db.models import Q,IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal

from companies.models import Company

# Create your models here.

class Item(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="items")

    stock_code_id = models.CharField(_("Stock Code ID"), max_length=25, null=True, blank=True)
    stock_code = models.CharField(_("Stock Code"), max_length=140, null=True, blank=True)
    stock_name = models.CharField(_("Stock Name"), max_length=250, null=True, blank=True)
    item_group_id = models.CharField(_("Item Group ID"), max_length=25, null=True, blank=True)
    item_group_code = models.CharField(_("Item Group Code"), max_length=140, null=True, blank=True)
    item_group_name = models.CharField(_("Item Group Name"), max_length=250, null=True, blank=True)
    item_group_type = models.CharField(_("Item Group Type"), max_length=50, null=True, blank=True)
    fixed_asset_group = models.CharField(_("Fixed Asset Group"), max_length=140, null=True, blank=True)
    explanation = models.CharField(_("Explanation"), max_length=250, null=True, blank=True)
    item_group_type_id = models.CharField(_("Item Group Type ID"), max_length=50, null=True, blank=True)
    bddk_code = models.CharField(_("BDDK Code"), max_length=140, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.stock_code) + " - " + str(self.stock_name)
    
