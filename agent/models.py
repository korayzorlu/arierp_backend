from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings


from django.utils.translation import gettext_lazy as _
import uuid

from common.models import Status,Currency
from companies.models import Company

# Create your models here.

class TimestampModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class AgentTask(TimestampModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="agent_tasks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_agent_tasks")
    STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('in_progress', ('In Progress')),
        ('completed', ('Completed')),
        ('rejected', ('Rejected'))
    )
    status = models.CharField(_("Status"), max_length=25, default='pending', choices=STATUS_CHOICES, blank=True, null=True)
    agent_name = models.CharField(_("Agent Name"), max_length=150, blank=True, null=True)
    lf_username = models.CharField(_("LF Username"), max_length=150, blank=True, null=True)
    lf_password = models.CharField(_("LF Password"), max_length=150, blank=True, null=True)
    file = models.FileField(upload_to="agent_tasks/", blank=True, null=True)
    log = models.TextField(_("Log"), max_length=10000, blank = True, null = True)

    def __str__(self):
        return str(f"{self.agent_name} - {self.user.get_full_name()}")