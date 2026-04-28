from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils import timezone

from common.utils.common_utils import LegacyTLSAdapter
from communication.models import SetrowEmail
from users.models import User
from companies.models import Company

import requests

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
                    company=company
                )
            