from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User

# Create your models here.

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, blank=True, related_name="subscription")

    SUBSCRIPTION_TYPES = [
        ('free', 'Free'),
        ('standart', 'Standart'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]

    type = models.CharField(_("Type"), max_length=25, default='free', choices=SUBSCRIPTION_TYPES, blank=True, null=True)

    duration = models.PositiveIntegerField(_("Duration"), default=30)
    startDate = models.DateTimeField(_("Start Date"), auto_now_add=True, null=True)
    endDate = models.DateTimeField(_("End Date"),blank=True, null=True)

    def __str__(self):
        return f"{self.type} | {self.user} | {self.user.get_full_name()}"