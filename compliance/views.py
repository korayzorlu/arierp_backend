from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utils.mixins import CompanyOwnershipRequiredMixin

from .models import *
import os
import json
import pandas as pd
from decimal import Decimal
from datetime import date,datetime

# Create your views here.

class UpdateThirdPersonStatusView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = ThirdPerson.objects.select_related().filter(uuid = data.get('uuid')).first()
        obj.status = data.get('status')
        obj.save()

        bank_activities = obj.bank_activities.select_related().all()
        for bank_activity in bank_activities:
            bank_activity.is_reliable_person = True if data.get('status') == 'cleared' else False
            bank_activity.third_person_status = data.get('status')
            bank_activity.save()

        return JsonResponse({'message': 'Durum değiştirildi!','status':'success'}, status=200)