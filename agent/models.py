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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="agent_tasks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_agent_tasks")
    task_id = models.CharField(_("Task ID"), max_length=250, unique=True)
    STATUS_CHOICES = (
        ('pending', ('Pending')),
        ('in_progress', ('In Progress')),
        ('completed', ('Completed')),
        ('rejected', ('Rejected'))
    )
    status = models.CharField(_("Status"), max_length=25, default='pending', choices=STATUS_CHOICES, blank=True, null=True)

    def __str__(self):
        return str(f"{self.task_id} - {self.user.get_full_name()}")