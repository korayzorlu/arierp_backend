from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import *

import json

# Create your views here.

class ReadNotificationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user = self.request.user)

        if notifications:
            notifications.update(is_read = True)

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)