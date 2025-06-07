from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User

# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank = True, null = True, related_name="notifications")
    title = models.CharField(max_length=100,null=True,blank=True)
    message = models.CharField(max_length=100,null=True,blank=True)
    navigation = models.CharField(max_length=100,null=True,blank=True)
    image = models.ImageField(_("Image"), upload_to='media/docs/notifications/ ', null=True, blank=True,
                              help_text=_("Please upload a square image, otherwise center will be cropped."))
    is_read = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return self.message