from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

import uuid

from common.models import Country

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name']

    is_email_verified = models.BooleanField(default=False)

    phone_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_users")
    phone_number = models.CharField(_("Phone Number"), max_length=25, blank=True, null=True)
    verify_sid = models.CharField(_("Verify SID"), max_length=50, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['phone_country', 'phone_number'], name='unique_phone_country_number')
        ]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, blank=True)

    image = models.ImageField(_("Image"), upload_to='media/docs/users/ ', null=True, blank=True,
                              help_text=_("Please upload a square image, otherwise center will be cropped."))

    THEME_CHOICES = (('dark', ('Dark')), ('light', ('Light')))
    theme = models.CharField(_("Theme"), max_length=25, default='light', choices=THEME_CHOICES, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.user} | {self.user.get_full_name()}"