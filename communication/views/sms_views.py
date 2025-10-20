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

from communication.models import SMS
from communication.utils.sms_utils import send_sms_with_turatel
from partners.models import Partner

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

class SendSMSView(LoginRequiredMixin,View):
    model = SMS

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        response = send_sms_with_turatel(data)

        return JsonResponse({'message': str(response),'status':'success'}, status=200)