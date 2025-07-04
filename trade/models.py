from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City
from partners.models import Partner

# Create your models here.

class TradeAccount(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="trade_accounts")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_trade_accounts", null=True, blank=True)
    account_id = models.CharField(_("Account ID"), max_length=25, blank=True, null=True)
    crm_id = models.CharField(_("CRM ID"), max_length=25, blank=True, null=True)
    crm_type = models.CharField(_("CRM Type"), max_length=25, blank=True, null=True)

    name = models.CharField(_("Name"), max_length=140, null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
# class Collection(models.Model):
#     uuid = models.UUIDField(default=uuid.uuid4, unique=True)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="trade_accounts")

#     partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_trade_accounts", null=True, blank=True)
#     account_id = models.CharField(_("Account ID"), max_length=25, blank=True, null=True)
#     crm_id = models.CharField(_("CRM ID"), max_length=25, blank=True, null=True)
#     crm_type = models.CharField(_("CRM Type"), max_length=25, blank=True, null=True)

#     name = models.CharField(_("Name"), max_length=140, null=True, blank=True)
    
#     created_date = models.DateTimeField(auto_now_add=True)
#     updated_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return str(self.name)