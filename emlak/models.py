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
from users.models import User

class RealEstateAgent(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="real_estate_agents")

    name = models.CharField(_("Real Estate Agent Name"), max_length=140, null=True, blank=True)

    phone_number_1 = models.CharField(_("Phone Number 1"), max_length=25, blank=True, null=True)
    phone_number_2 = models.CharField(_("Phone Number 2"), max_length=25, blank=True, null=True)

    url = models.CharField(_("URL"), max_length=500, blank=True, null=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

class WhatsappMessage(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="whatsapp_messages")
    
    real_estate_agent = models.ForeignKey(RealEstateAgent, on_delete=models.CASCADE, related_name="real_estate_agent_whatsapp_messages", null=True, blank=True)

    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.real_estate_agent.name} - {self.real_estate_agent.phone_number_1}")
