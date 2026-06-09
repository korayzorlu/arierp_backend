from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils import timezone

from common.utils.common_utils import LegacyTLSAdapter
from communication.models import SetrowEmail
from users.models import User
from companies.models import Company,UserCompany

import requests
import xmltodict
import json

def send_email_for_lease_changes(name,tc_vkn_no):       
    def send_outlook_email(subject, message, from_email, recipient_list, attachments=None):
        email = EmailMessage(
            subject,
            message,
            from_email,
            recipient_list,
        )
        if attachments:
            for attachment in attachments:
                email.attach(attachment['name'], attachment['content'], attachment['mimetype'])
        email.send(fail_silently=False)
        #send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            
    subject = '3. ŞAHIS ÖDEMESİ - KONTROL GEREKİYOR'
    message = f'''
        Aşağıdaki kişi/kurum için yasaklı liste kontrolü gerekmektedir. Lütfen kontrol ediniz.

        {name} - {tc_vkn_no}

        Arınet 3. Şahıs Kontrol Ekranı: https://arinet.arileasing.com.tr/third-persons

    '''
    from_email = 'Arınet <noreply@arileasing.com.tr>'
    recipient_list = settings.THIRD_PERSON_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)

def send_email_with_setrow(params):
    company = Company.objects.filter(uuid=params.get("company_id")).first()
    user = User.objects.filter(uuid=params.get("user_id")).first()

    url = f"https://www.setrowsend.com/email/sendV2.php?k={settings.SETROW_API_KEY}&ktemplate={params.get('template')}"

    headers = {
        "Authorization": f"Bearer {settings.SETROW_API_KEY}",
    }

    payload = []

    for recipient in params.get('recipients', []):
        payload.append({
            "to": recipient.get('email'),
            "variables": recipient.get('variables', {}),
        })

    session = requests.Session()
    session.mount("https://", LegacyTLSAdapter())

    chunk_size = 1000
    for i in range(0, max(len(payload), 1), chunk_size):
        chunk = payload[i:i + chunk_size]
        response = session.post(url, headers=headers, json=chunk)
        if response.text:
            response_data = response.json()
            for data in response_data.get("message", []):
                SetrowEmail.objects.create(
                    send_id=data.get("send_id"),
                    sender='iletisim@mail.info.arileasing.com.tr',
                    recipient=data.get("email"),
                    status=params.get('status'),
                    send_date=timezone.now(),
                    user=user,
                    company=company,
                    template=params.get('template_name'),
                )

def send_email_global_with_setrow(params):
    user = User.objects.filter(uuid=params.get("user_id")).first()
    active_company = UserCompany.objects.filter(uuid=params.get('activeCompany'), is_active=True).first()
    company = active_company.company if active_company else None

    url = f"https://www.setrowsend.com/email/sendV2.php?k={settings.SETROW_API_KEY}&ktemplate={params.get('template')}"

    headers = {
        "Authorization": f"Bearer {settings.SETROW_API_KEY}",
    }

    payload = []

    for recipient in params.get('recipients', []):
        payload.append({
            "to": recipient.get('to'),
            "variables": recipient.get('variables', {}),
        })

    # print(payload)
    # print("------------------------------")

    session = requests.Session()
    session.mount("https://", LegacyTLSAdapter())

    chunk_size = 1000
    for i in range(0, max(len(payload), 1), chunk_size):
        chunk = payload[i:i + chunk_size]
        response = session.post(url, headers=headers, json=chunk)
        if response.text:
            response_data = response.json()
            for data in response_data.get("message", []):
                SetrowEmail.objects.create(
                    send_id=data.get("send_id"),
                    sender='iletisim@mail.info.arileasing.com.tr',
                    recipient=data.get("email"),
                    status=params.get('status'),
                    send_date=timezone.now(),
                    user=user,
                    company=company,
                    template=params.get('template_name'),
                )

def check_last_email(email):
    last_email = SetrowEmail.objects.filter(
        recipient = email,
        send_date__gte = timezone.now() - timezone.timedelta(hours=1)
    ).first()
    
    if last_email:
        return True
    return False

def fetch_email_reports_with_setrow(params,BATCH_SIZE=1000):
    company_obj = Company.objects.select_related().filter(id=int(params.get("company"))).first()

    date = params.get("date") if params.get("date") != "" else timezone.now().strftime("%Y-%m-%d")
    templatename = f"&templatename_id={params.get('template')}" if params.get("template") != "" else ""

    url = (
        f"https://api.setrow.com/V1/TRANS_SONUC_V2.php"
        f"?apikey={settings.SETROW_API_KEY}"
        f"&date={date}"
        f"&type=2"
        f"{templatename}"
    )

    headers = {
        "Authorization": f"Bearer {settings.SETROW_API_KEY}",
    }

    session = requests.Session()
    session.mount("https://", LegacyTLSAdapter())

    response = session.post(url, headers=headers)

    data_dict = xmltodict.parse(response.content)
    data_json = json.dumps(data_dict, ensure_ascii=False, indent=2)

    if data_dict.get("TRANS_SONUC_V2_XML", {}).get("SETROW_SONUC", {}):
        data = data_dict.get("TRANS_SONUC_V2_XML", {}).get("SETROW_SONUC", {}).get("SETROW_SONUC_NODE", [])
    else:
        data = []

    #örnek rapor
    # {

    #     "SETROW_TEMPLATE_ID": "271122",

    #     "SABLON_ADI": "vadesi_gecmisler",

    #     "GONDERIM_ID": "fe4f1877017eeb0388de",

    #     "EMAIL_ADRESI": "kubilay.acar@tugba.com",

    #     "GONDERIM_TARIHI": "2026-04-29 10:35:19",

    #     "GORUNTULEME": "0",

    #     "GORUNTULEME_TARIHI": null,

    #     "TIKLAMA": "0",

    #     "TIKLAMA_TARIHI": null,

    #     "GLOBAL_HATALI_ADRES": "0",

    #     "HATALI_ADRES": "0",

    #     "BULTEN_ISTEMEYEN_ADRES": "0",

    #     "JUNK_ADRES": "0",

    #     "MUSTERI_GONDERIM_ID": null,

    #     "GORUNTULEME_SAYISI": "0",

    #     "TIKLAMA_SAYISI": "0",

    #     "GONDERI_DURUMU": "1"

    # }

    updated_records = 0

    for report in data:
        SetrowEmail.objects.update_or_create(
            send_id = report.get("GONDERIM_ID"),
            defaults={
                "sender": "iletisim@mail.info.arileasing.com.tr",
                "recipient": report.get("EMAIL_ADRESI"),
                "send_date": timezone.make_aware(timezone.datetime.strptime(report.get("GONDERIM_TARIHI"), "%Y-%m-%d %H:%M:%S")),
                "company": company_obj,
                "send_status": str(report.get("GONDERI_DURUMU")),
                "template": report.get("SABLON_ADI"),
            }
        )
        updated_records += 1
    
    print(f"Updated {updated_records} records.")