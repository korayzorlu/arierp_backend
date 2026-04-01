from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utils.mixins import CompanyOwnershipRequiredMixin

from leasing.models import *

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

class AddLeaseNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        lease = Lease.objects.select_related().filter(uuid=data.get('lease_id')).first()

        LeaseNote.objects.create(
            company = company,
            title = data.get('data').get('title'),
            text = data.get('data').get('text'),
            lease = lease,
            user = request.user
        )

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)

class UpdateLeaseNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = LeaseNote.objects.filter(uuid = data.get('data').get('uuid')).first()
        obj.title = data.get('data').get('title')
        obj.text = data.get('data').get('text')
        obj.save()

        return JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
    
class DeleteLeaseNoteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = LeaseNote.objects.filter(uuid = data.get('data').get('uuid')).first()
        obj.delete()

        return JsonResponse({'message': 'Başarıyla silindi!','status':'success'}, status=200)

