from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from django.utils.translation import gettext_lazy as _
import uuid

from companies.models import Company

# Create your models here.

class Category(MPTTModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="categories")

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    name = models.CharField(_("Name"), max_length=150, null=True, blank=True, db_index=True)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.name)

class Product(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="products")

    name = models.CharField(_("Name"), max_length=150, null=True, blank=True, db_index=True)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.name)