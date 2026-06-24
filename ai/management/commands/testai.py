from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from leasing.tasks import fetch_leases

import pandas as pd
import json
import os
import pyodbc
import ollama
import time

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")

        start = time.time()
        client = settings.AI_CLIENT
        
        response = client.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",          # ← Bu system prompt
                    "content": "Sen bir Türk ERP, CRM asistanısın. Yalnızca Türkçe yanıt ver. Aynı zamanda finansal kiralama alanında uzman bir danışmansın. Kullanıcıya doğru ve net yanıtlar ver. Yanıt verirken örnekler vererek açıklayıcı ol. Gereksiz detaylara girmeden kısa ve öz yanıt ver."
                },
                {
                    "role": "user",            # ← Bu kullanıcının sorusu
                    "content": "Merhaba, ödeme planına uymayan bir müşteri icra verilebilir mi? finansal kiralama sözleşmelerinde icra süreci nasıl işler? örneklerle açıkla."
                }
            ]
        )

        answer = response.message.content

        print(answer)
        print(f"Süre: {time.time() - start:.2f}s")
        print("done!")