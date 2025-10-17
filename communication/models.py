from django.db import models, transaction
from django.db.models import Q,IntegerField
from django.db.models.functions import Cast
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings

from django.utils.translation import gettext_lazy as _
import uuid
from decimal import Decimal
import re
from itertools import chain
from datetime import datetime,timedelta
import requests
from requests.auth import HTTPBasicAuth
import ollama

from underwriting.utils import check_third_person_status
from companies.models import Company
from common.models import Currency, Status
from common.utils.ai_utils import EXAMPLE_DEF,EXAMPLE_LIST
from partners.models import Partner

# Create your models here.

class SMS(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="smss")
    
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="partner_smss", null=True, blank=True)
    packet_id = models.CharField(_("Packet ID"), max_length=50, null=True, blank=True)
    message_id = models.CharField(_("Message ID"), max_length=50, null=True, blank=True)
    reference_id = models.CharField(_("Reference ID"), max_length=50, null=True, blank=True)
    error_code = models.CharField(_("Error Code"), max_length=25, null=True, blank=True)
    size = models.CharField(_("Size"), max_length=25, null=True, blank=True)
    STATUS_CHOICES = (
        ('0', ('İletildi')),
        ('1', ('İletilemedi')),
        ('2', ('Beklemede')),
    )
    status = models.CharField(_("Status"), max_length=25, default='0', choices=STATUS_CHOICES, blank=True, null=True)
    reason = models.CharField(_("Reason"), max_length=250, null=True, blank=True)

    CATEGORY_CHOICES = (
        ('default', ('Standart')),
        ('risk', ('Vadesi Geçmiş')),
        ('to_warned', ('İhtar Çekilecek')),
        ('warned', ('İhtar Çekilen')),
        ('to_terminated', ('Fesih Edilecek')),
        ('today_payment', ('Bugün Ödemesi Olan')),
        ('tomorrow_payment', ('Yarın Ödemesi Olan')),
    )
    category = models.CharField(_("Category"), max_length=25, default='0', choices=CATEGORY_CHOICES, blank=True, null=True)

    send_date = models.DateTimeField(_("Send Date"), blank=True, null=True)
    delivery_date = models.DateTimeField(_("Delivery Date"), blank=True, null=True)
    text = models.CharField(_("Text"), max_length=500, null=True, blank=True)
    phone_number = models.CharField(_("Phone Number"), max_length=140, null=True, blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.phone_number} - {self.text}")  