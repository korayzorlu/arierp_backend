from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from communication.utils.turatel_utils import *
from contracts.models import *
from leasing.models import *
from accounting.tasks import fetch_trial_balances

from emlak.utils import send_test_wb_message

import pandas as pd
import json
import os
import pyodbc
import requests
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

        TOKEN = "EAAYvKmF1R8YBSlRAf6QCCZB46rOqcu75ctW7rx1HyDSU5pqvVPhZCOtaFYJOlZB0TySoUU4H9ZCMZBq0qXaSZCSEKKr3GA7I6cTL6VzOXyCm2G4VFPMjKFJZCqgrLi2wVBYSBj9iv535KYIipTAYlBGc8ZBGQUkRe1ylsNp058RQKXzYl61Wcenj74FcZBveEcKoq5gW9YYxSeuGbve7Por4dyFbWfYAb0atBsEnzJTVFqPzNiLiqRHwFf3rzcOnegk3QuRghteZCr7mvNP8P6heCxKkmZA"
        WABA_ID = "1629363698545041"
        PHONE_NUMBER_ID = "1354229851098045"
        APP_SECRET='6779344db10d72ebd8973e13d93f0598'

        # now = int(time.time())
        # start = now - 7200  # son 2 saat

        # r = requests.get(f"https://graph.facebook.com/v26.0/{WABA_ID}",
        #     params={
        #         "fields": f"conversation_analytics.start({start}).end({now}).granularity(HALF_HOUR).phone_numbers(['+905386460823']).dimensions(['CONVERSATION_DIRECTION'])",
        #     },
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        # )
        # print(r.json())




        # print(requests.get(
        #     "https://graph.facebook.com/v26.0/1629363698545041",
        #     params={"fields": "id,name,subscribed_apps,webhook_configuration"},
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        # ).json())

        # print(requests.get(
        #     "https://graph.facebook.com/v26.0/1354229851098045",
        #     params={"fields": "webhook_configuration"},
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
        # ).json())


        # r = requests.post(
        #     f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/settings",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        #     params={
        #         "override_callback_uri": "https://emlak.arileasing.com.tr/api/communication/whatsapp_webhook/",
        #         "verify_token": settings.WB_VERIFY_TOKEN,
        #     },
        # )
        # print(r.status_code, r.json())





        # # override'ı kaldır (DELETE)
        # r = requests.delete(f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/settings",
        #     params={"include_webhooks": "true"},
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
        # print("DELETE:", r.status_code, r.json())

        # # tüm ayarları ham haliyle gör
        # r2 = requests.get(f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/settings",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
        # print("SETTINGS:", r2.status_code, r2.json())





        # r = requests.post(f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/deregister",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
        # print(r.status_code, r.json())


        # r = requests.post(f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/register",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        #     json={"messaging_product": "whatsapp", "pin": "681215"})
        # print(r.status_code, r.json())

        # r = requests.post(f"https://graph.facebook.com/v26.0/1629363698545041/subscribed_apps",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        # )
        # print(r.status_code, r.json())



        # print("SUB:", requests.get(f"https://graph.facebook.com/v26.0/{WABA_ID}/subscribed_apps", headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}).json())

        # # 2) Aboneliği (yeniden) kur
        # print("SUBPOST:", requests.post(f"https://graph.facebook.com/v26.0/{WABA_ID}/subscribed_apps", headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}).json())

        # # 3) Register tazele
        # print("REG:", requests.post(f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/register",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}, json={"messaging_product": "whatsapp", "pin": "681215"}).json()
        # )


        # WABA seviyesinde override webhook'u temizle -> App-level config'e düşsün
        # print(requests.post("https://graph.facebook.com/v26.0/1629363698545041/subscribed_apps",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        #     json={
        #         "override_callback_uri": "https://emlak.arileasing.com.tr/api/communication/whatsapp_webhook/",
        #         "verify_token": settings.WB_VERIFY_TOKEN
        #     }
        # ).json())


        # # Önce çıkar
        # print("DEL:", requests.delete("https://graph.facebook.com/v26.0/1629363698545041/subscribed_apps",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}).json())
        # # Tekrar ekle
        # print("ADD:", requests.post("https://graph.facebook.com/v26.0/1629363698545041/subscribed_apps",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}).json())



        # print(requests.get("https://graph.facebook.com/v26.0/1354229851098045",
        #     params={"fields": "webhook_configuration,status,platform_type,throughput,last_onboarded_time"},
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}).json()
        # )




        # r = requests.get(
        #     f"https://graph.facebook.com/v26.0/{WABA_ID}/phone_numbers",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        #     params={"fields": "id,display_phone_number,platform_type,status,webhook_configuration"}
        # )
        # print(r.status_code, r.json())





        # r = requests.post(
        #     f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/register",
        #     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        #     json={"messaging_product": "whatsapp", "pin": "681215"},
        # )
        # print(r.status_code, r.json())



        # r = requests.get(
        #     f"https://graph.facebook.com/v26.0/1740708930471878/subscriptions",
        #     params={"access_token": f"1740708930471878|{APP_SECRET}"},
        #     data={
        #         "object": "whatsapp_business_account",
        #         "callback_url": "https://emlak.arileasing.com.tr/api/communication/whatsapp_webhook/",
        #         "verify_token": settings.WB_VERIFY_TOKEN,
        #         "fields": "messages",
        #     }
        # )
        # print(r.status_code, r.json())



        # r = requests.get(
        #     f"https://graph.facebook.com/v26.0/{WABA_ID}/subscribed_apps",
        #     headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        # )
        # print(r.status_code, r.json())



        # r = requests.get("https://graph.facebook.com/v26.0/oauth/access_token", params={
        #     "grant_type": "fb_exchange_token",
        #     "client_id": "1740708930471878",
        #     "client_secret": APP_SECRET,
        #     "fb_exchange_token": TOKEN,
        # })
        # print(r.json())



        MY_NUMBER = "905542663970"
        PIN = "681215"  # kendin belirle, not al
        BASE = "https://graph.facebook.com/v26.0"
        H = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

        # # phone number id
        # r = requests.get(f"{BASE}/{WABA_ID}/phone_numbers", headers=H).json()
        # print("phone_numbers:", r)
        # pn = r["data"][0]
        # PHONE_NUMBER_ID = pn["id"]

        # # register (gerekirse)
        # if pn.get("platform_type") != "CLOUD_API":
        #     print("register:", requests.post(f"{BASE}/{PHONE_NUMBER_ID}/register", headers=H,
        #         json={"messaging_product": "whatsapp", "pin": PIN}).json())

        # # app'i webhook'a abone et
        # print("subscribe:", requests.post(f"{BASE}/{WABA_ID}/subscribed_apps", headers=H).json())

        # test mesajı
        # print("send:", requests.post(f"{BASE}/{PHONE_NUMBER_ID}/messages", headers=H, json={
        #     "messaging_product": "whatsapp",
        #     "to": MY_NUMBER,
        #     "type": "text",
        #     "text": {"body": "API test mesajı - Arı Leasing"},
        # }).json())
        # print("PHONE_NUMBER_ID =", PHONE_NUMBER_ID)


        send_test_wb_message()


        # r = requests.get(f"{BASE}/1629363698545041/message_templates",
        #     params={"name": "emlak", "fields": "name,language,status,components"},
        #     headers=H
        # )
        # print(r.json())

        # print(requests.get("https://graph.facebook.com/v26.0/1629363698545041/subscribed_apps", headers=H).json())
        # print(requests.get("https://graph.facebook.com/v26.0/1354229851098045", params={"fields": "webhook_configuration"}, headers=H).json())
  
        
        print("done!")