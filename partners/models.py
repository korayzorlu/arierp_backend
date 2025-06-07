from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City

# Create your models here.

class Partner(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partners")

    name = models.CharField(_("Partner Name"), max_length=140)
    formal_name = models.CharField(_("Partner Formal Name"), max_length=140)
    image = models.ImageField(_("Image"), upload_to='media/docs/partners/ ', null=True, blank=True,
                              help_text=_("Please upload a square image, otherwise center will be cropped."))
    
    TYPES_CHOICES = (
        ('customer', ('Customer')),
        ('supplier', ('Supplier')),
        ('shareholder', ('Shareholder')),
    )
    types = ArrayField(models.CharField(_("Status"), max_length=25, choices=TYPES_CHOICES), default=list, blank=True, null=True)
    vat_office = models.CharField(_("Vat Office"), max_length=50, blank=True, null=True)
    vat_no = models.CharField(_("Vat No"), max_length=50, blank=True, null=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_partners")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="city_partners")
    address = models.CharField(_("Address"), max_length=150, blank=True, null=True)
    address2 = models.CharField(_("Address 2"), max_length=150, blank=True, null=True)
    is_billing_same = models.BooleanField(default=False)
    billing_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="billing_country_partners")
    billing_city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="billing_city_partners")
    billing_address = models.CharField(_("Billing Address"), max_length=150, blank=True, null=True)
    billing_address2 = models.CharField(_("Billing Address 2"), max_length=150, blank=True, null=True)

    phone_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="phone_country_partners")
    phone_number = models.CharField(_("Phone Number"), max_length=25, blank=True, null=True)
    email = models.EmailField(_("Email"), max_length=100, blank=True, null=True)
    web = models.CharField(_("Web"), max_length=250, blank=True, null=True)

    about = models.TextField(_("About"), blank = True, null = True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.formal_name is None:
            self.formal_name = self.name
        super(Partner, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

