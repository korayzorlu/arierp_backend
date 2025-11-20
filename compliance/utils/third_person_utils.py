import json
from compliance.models import ThirdPerson
from django.core.mail import EmailMessage, send_mail
from django.conf import settings

import re

def create_third_person(self,scan_result):
        if self.name is not None and self.name != "" and self.name != "None":
            name = self.name
        else:
            catched_name = re.search(r"-\s*(.*?)\s*-", self.description)
            if catched_name:
                name = catched_name.group(1)
            else:
                name = ""

        if scan_result["status"] == 'cleared':
            status = 'need_document'
        else:
            status = 'pending'
            
        if name and name != "" and status == 'pending':
            send_email_for_third_person(name,self.tc_vkn_no)

        if name and name != "" and status == 'need_document':
            send_email_for_third_person_document(name,self.tc_vkn_no)
        
        old_obj = ThirdPerson.objects.filter(company = self.company, tc_vkn_no = self.tc_vkn_no, name = name).first()
        if not old_obj:
            new_obj = ThirdPerson.objects.create(
                company=self.company,
                name=name,
                tc_vkn_no=self.tc_vkn_no,
                status=status,
                results=scan_result["details"] if scan_result["details"] else None
            )

            new_obj.bank_activities.add(self)
            new_obj.save()
        else:
            old_obj.bank_activities.add(self)
            old_obj.save()

def send_email_for_third_person(name,tc_vkn_no):       
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

def send_email_for_third_person_document(name,tc_vkn_no):       
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
            
    subject = '3. ŞAHIS ÖDEMESİ - BELGE/KİMLİK GEREKİYOR'
    message = f'''
        Aşağıdaki kişi/kurum için belge/kimlik yüklenmesi gerekmektedir. Lütfen kontrol ediniz.

        {name} - {tc_vkn_no}

        Arınet 3. Şahıs Kontrol Ekranı: https://arinet.arileasing.com.tr/third-persons

    '''
    from_email = 'Arınet <noreply@arileasing.com.tr>'
    recipient_list = settings.THIRD_PERSON_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)