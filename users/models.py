from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

import uuid

from common.models import Country

class EventType(models.TextChoices):
    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILED = "login_failed", "Login Failed"
    LOGOUT = "logout", "Logout"

class FailReason(models.TextChoices):
    BAD_CREDENTIALS = "bad_credentials", "Hatalı kullanıcı adı/şifre"
    INACTIVE = "inactive", "Pasif kullanıcı"
    LOCKED = "locked", "Hesap kilitli"
    OTHER = "other", "Diğer"

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email','first_name','last_name']

    is_email_verified = models.BooleanField(default=False)

    phone_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_users")
    phone_number = models.CharField(_("Phone Number"), max_length=25, blank=True, null=True)
    verify_sid = models.CharField(_("Verify SID"), max_length=50, blank=True, null=True)
    leaseflex_id = models.CharField(_("Leaseflex ID"), max_length=50, blank=True, null=True)
    position = models.CharField(_("Position"), max_length=255, blank=True, null=True)

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

class AuthEvent(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_auth_events",blank=True, null=True)
    event_type =  models.CharField(_("Event Type"), max_length=25, choices=EventType.choices, blank=True, null=True)

    username_attempted  = models.CharField(_("Username Attempt"), max_length=140, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(_("User Agent"), max_length=500, null=True, blank=True)

    failure_reason =  models.CharField(_("Failure Reason"), max_length=25, choices=FailReason.choices, blank=True, null=True)
    date = models.DateTimeField(_("Date"), auto_now_add=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.event_type) + " | " + str(self.date)

