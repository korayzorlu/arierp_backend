from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum,Count,Case,When,Value,BooleanField,Max
from django.views import View
from django.http import HttpResponseForbidden, JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from utils.mixins import CompanyOwnershipRequiredMixin

from communication.models import WhatsAppContact,WhatsAppMessage

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime

@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    def get(self, request, *args, **kwargs):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.WB_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        print(data)

        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    contacts = value.get("contacts", [])
                    messages = value.get("messages", [])
                    for contact in contacts:
                        WhatsAppContact.objects.update_or_create(
                            phone_number=contact.get("wa_id"),
                            name=contact.get("profile", {}).get("name"),
                            wa_id=contact.get("wa_id")
                        )

                    for message in messages:
                        contact = WhatsAppContact.objects.filter(wa_id=message.get("from")).first()

                        if contact:
                            WhatsAppMessage.objects.create(
                                contact=contact,
                                wa_message_id=message.get("id"),
                                message_type=message.get("type"),
                                message_time=datetime.fromtimestamp(int(message.get("timestamp"))),
                                text=message.get("text", {}).get("body")
                            )

        

        return HttpResponse(status=200)