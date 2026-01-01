from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company
from common.models import Country,City
from users.models import User

# Create your models here.

class Sector(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sectors")

    code = models.CharField(_("Code"), max_length=50)
    name = models.CharField(_("Name"), max_length=250)

    main_sector_code = models.CharField(_("Main Sector Code"), max_length=50, null=True, blank=True)
    match_code = models.CharField(_("Match Code"), max_length=50, null=True, blank=True)
    kkbmb_sector_code = models.CharField(_("KKBMB Sector Code"), max_length=50, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

class Partner(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partners")

    first_name = models.CharField(_("First Name"), max_length=140, blank=True, null=True)
    last_name = models.CharField(_("Last Name"), max_length=140, blank=True, null=True)

    name = models.CharField(_("Partner Name"), max_length=140, null=True, blank=True)
    formal_name = models.CharField(_("Partner Formal Name"), max_length=140, null=True, blank=True)
    image = models.ImageField(_("Image"), upload_to='media/docs/partners/ ', null=True, blank=True,
                              help_text=_("Please upload a square image, otherwise center will be cropped."))
    
    TYPES_CHOICES = (
        ('customer', ('Customer')),
        ('supplier', ('Supplier')),
        ('shareholder', ('Shareholder')),
        ('special', ('Special')),
        ('pep', ('PEP')),
        ('barter', ('Barter')),
        ('virman', ('Virman')),
    )
    types = ArrayField(models.CharField(_("Status"), max_length=25, choices=TYPES_CHOICES), default=list, blank=True, null=True)

    CUSTOMER_TYPES_CHOICES = (
        ('individual', ('Individual')),
        ('institutional', ('Institutional')),
    )
    customer_type = models.CharField(_("Customer Type"), max_length=25, default='individual', choices=CUSTOMER_TYPES_CHOICES, blank=True, null=True)

    customer_code = models.CharField(_("Customer Code"), max_length=25, blank=True, null=True)
    crm_code = models.CharField(_("CRM Code"), max_length=25, blank=True, null=True)


    vat_office = models.CharField(_("Vat Office"), max_length=50, blank=True, null=True)
    vat_no = models.CharField(_("Vat No"), max_length=50, blank=True, null=True)
    tc_no = models.CharField(_("TC No"), max_length=50, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)
    passport_no = models.CharField(_("Passport No"), max_length=50, blank=True, null=True)

    ticari_sicil_no = models.CharField(_("Ticari Sicil No"), max_length=50, blank=True, null=True)
    kep = models.CharField(_("Kep"), max_length=140, blank=True, null=True)
    kep_expiry_date = models.DateField(_("Kep Expiry Date"), blank=True, null=True)
    is_turkkep = models.BooleanField(default=False)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="sector_partners", blank=True, null=True)

    father_name = models.CharField(_("Father Name"), max_length=140, blank=True, null=True)
    birthday = models.DateField(_("Birthday"), blank=True, null=True)
    birth_place = models.CharField(_("Birth Place"), max_length=140, blank=True, null=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_partners")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="city_partners")
    address = models.CharField(_("Address"), max_length=250, blank=True, null=True)
    address2 = models.CharField(_("Address 2"), max_length=250, blank=True, null=True)
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

    advance_amount = models.DecimalField(_("Advance Amount"), default = 0.00, max_digits=14, decimal_places=2)

    is_scan = models.BooleanField(default=False)
    last_scan_date = models.DateTimeField(_("Last Scan Date"), blank=True, null=True)
    next_scan_date = models.DateTimeField(_("Next Scan Date"), blank=True, null=True)
    is_reliable_person = models.BooleanField(default=False)
    is_commercial = models.BooleanField(default=False)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.formal_name is None:
            self.formal_name = self.name
        super(Partner, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

class PartnerNote(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_notes")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True, related_name="partner_partner_notes")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="user_partner_notes")
    title = models.CharField(_("Title"), max_length=140, blank=True, null=True)
    text = models.CharField(_("Text"), max_length=1000, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.user.get_full_name()} - {self.title}")