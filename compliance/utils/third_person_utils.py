from django.db.models import Q

import json
from compliance.models import ThirdPerson
from django.core.mail import EmailMessage, send_mail
from django.conf import settings

import re
import time

from partners.models import Partner

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
        send_email_for_third_person(name,self.tc_vkn_no or "")

    if name and name != "" and status == 'need_document':
        send_email_for_third_person_document(name,self.tc_vkn_no or "")
    
    #old_obj = ThirdPerson.objects.filter(company = self.company, tc_vkn_no = self.tc_vkn_no, name = name, is_vpos=self.is_vpos).first()
    old_obj = ThirdPerson.objects.filter(tc_vkn_no = self.tc_vkn_no).first()
    if old_obj:
        old_obj.bank_activities.add(self)
        old_obj.save()

        return {"is_new": False, "status": old_obj.status}
    else:
        new_obj = ThirdPerson.objects.create(
            company=self.company,
            name=name,
            tc_vkn_no=self.tc_vkn_no,
            status=status,
            results=scan_result["details"] if scan_result["details"] else None,
            #is_vpos = self.is_vpos
        )

        new_obj.bank_activities.add(self)
        new_obj.save()

        return {"is_new": True, "status": new_obj.status}
    
def create_third_person_vpos(name,company,tc_vkn_no,scan_result):
    if scan_result["status"] == 'cleared':
        status = 'need_document'
    else:
        status = 'pending'
    
    old_obj = ThirdPerson.objects.filter(company = company, tc_vkn_no = tc_vkn_no, name = name).first()
    if not old_obj:
        new_obj = ThirdPerson.objects.create(
            company=company,
            name=name,
            tc_vkn_no=tc_vkn_no,
            status=status,
            results=scan_result["details"] if scan_result["details"] else None
        )

        return {"is_new": True, "status": new_obj.status}
    else:

        return {"is_new": False, "status": old_obj.status}

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
    recipient_list = settings.THIRD_PERSON_DOCUMENT_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)

def send_email_for_third_person_cleared(name,tc_vkn_no):       
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
            
    subject = '3. ŞAHIS ÖDEMESİ - BELGE/KİMLİK EKLENDİ'
    message = f'''
        Aşağıdaki kişi/kurum için gerekli olan belge/kimlik sisteme eklenmiştir. Lütfen tahsilat işleminizi kontrol ediniz.

        {name} - {tc_vkn_no}

        Arınet Tahsilat İşleme Ekranı: https://arinet.arileasing.com.tr/collections

    '''
    from_email = 'Arınet <noreply@arileasing.com.tr>'
    recipient_list = settings.THIRD_PERSON_CLEARED_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)

def send_email_for_third_person_to_cleared(name,tc_vkn_no):       
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
            
    subject = '3. ŞAHIS ÖDEMESİ - TAMAMLANDI'
    message = f'''
        Aşağıdaki kişi/kurum için gerekli olan sorgu tamamlanmıştır. Lütfen tahsilat işleminizi kontrol ediniz.

        {name} - {tc_vkn_no}

        Arınet Tahsilat İşleme Ekranı: https://arinet.arileasing.com.tr/collections

    '''
    from_email = 'Arınet <noreply@arileasing.com.tr>'
    recipient_list = settings.THIRD_PERSON_CLEARED_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)

def check_third_person_in_partners():
    objs = ThirdPerson.objects.select_related().filter(
        (
            Q(status = 'pending') |
            Q(status = 'need_document')
        ) &
        Q(is_vpos = False)
    )
    for obj in objs:
        check_partners = Partner.objects.select_related().filter(
            (
                Q(tc_vkn_no=obj.tc_vkn_no) |
                Q(vat_no=obj.tc_vkn_no)
            ) &
            ~Q(tc_vkn_no__startswith='9999')
        )
        if check_partners.exists() and obj.tc_vkn_no and obj.tc_vkn_no != "":
            print(check_partners)
            obj.status = 'cleared'
            obj.save()
            bank_activities = obj.bank_activities.select_related().all()
            for bank_activity in bank_activities:
                bank_activity.is_reliable_person = True
                bank_activity.third_person_status = 'cleared'
                bank_activity.save()
            # bank_activities.update(
            #     is_reliable_person = True,
            #     third_person_status = 'cleared'
            # )
            send_email_for_third_person_to_cleared(obj.name,obj.tc_vkn_no)

        time.sleep(1)   