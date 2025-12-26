from django.core.mail import EmailMessage, send_mail
from django.conf import settings

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