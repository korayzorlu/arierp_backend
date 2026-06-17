from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings


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
    
class ThirdPerson(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="third_persons")

    name = models.CharField(_("Name"), max_length=250, null=True, blank=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=500, null=True, blank=True)
    card_no = models.CharField(_("Card No"), max_length=50, null=True, blank=True)

    STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('cleared', ('Cleared')),
        ('flagged', ('Flagged')),
        ('need_document', ('Need Document')),
        ('collection_denied', ('Collection Denied')),
    )
    status = models.CharField(_("Status"), max_length=25, default='pending', choices=STATUS_CHOICES, blank=True, null=True)

    bank_activities = models.ManyToManyField('leasing.BankActivity',related_name='bank_activities_third_persons', blank = True)
    results = models.JSONField(_("Results"), null=True, blank=True)
    is_vpos = models.BooleanField(default=False)

    is_email_sent = models.BooleanField(default=False)
    is_customer_sent = models.BooleanField(default=False)
    customer_sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_sender_third_persons", null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.name} - {self.tc_vkn_no}")
    
class ThirdPersonDocument(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="third_person_documents")

    third_person = models.ForeignKey(ThirdPerson, on_delete=models.CASCADE, related_name="third_person_third_person_documents", null=True, blank=True)
    label = models.CharField(_("Label"), max_length=250, null=True, blank=True)
    file = models.FileField(_("File"), upload_to='docs/compliance/third_person/documents/', null=True, blank=True, help_text=_("Please upload a file."))

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.label}")
    
    