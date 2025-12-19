from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import EmailMessage, send_mail, EmailMultiAlternatives

from contracts.models import *
from finance.models import *
from finance.tasks import add_finekra_bank_accounts
from compliance.models import ThirdPerson

import pandas as pd
import json
import os
import pyodbc
import requests

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def handle(self, *args, **options):
        print("processing...")

        excel_file = pd.ExcelFile("files/email-list.xlsx")
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel("files/email-list.xlsx", sheet_name)
        df = pd.DataFrame(file_data)

        email_list = df['email'].tolist()

        message = f'''
            <p>Değerli Müşterimiz,</p>

            <p>Arı Finansal Kiralama A.Ş. olarak, sizlere sunduğumuz hizmetlerde uzun yıllardır müşteri memnuniyetini önceliklendiren bir yaklaşım benimsemekteyiz. Bu anlayış doğrultusunda, bugüne kadar kredi kartı ile gerçekleştirilen ödemelerde oluşan banka ve ödeme sistemi kaynaklı komisyon bedelleri tarafımızca karşılanmıştır.</p>
            
            <p>Son dönemde finansal koşullarda yaşanan gelişmeler ve kredi kartı işlemlerine ilişkin banka komisyon oranlarının artması nedeniyle, söz konusu maliyetlerin şirketimiz tarafından karşılanmaya devam edilmesi ne yazık ki sürdürülebilir olmaktan çıkmıştır.</p>
            
            <p>Bu nedenle, 01 Ocak 2026 tarihinden itibaren, kredi kartı ile yapılacak ödemelerde uygulanacak kredi kartı komisyon oranı ilgili banka ve ödeme kuruluşları tarafından belirlenecek ve komisyon bedeli doğrudan banka tarafından tahsil edilecektir. Arı Finansal Kiralama A.Ş.’nin bu oranların belirlenmesinde herhangi bir yetkisi bulunmadığını ve tahsil edilen komisyon bedelinin şirketimiz için bir gelir niteliği taşımadığını özellikle belirtmek isteriz.</p>
            
            <p>Bu düzenleme, hizmetlerimizin kesintisiz ve sağlıklı şekilde sürdürülebilmesi amacıyla yapılmış olup, havale ve EFT gibi banka komisyonu doğurmayan ödeme yöntemlerinde herhangi bir değişiklik söz konusu değildir.</p>
            
            <p>Karşılıklı anlayış ve iş birliğimiz çerçevesinde göstereceğiniz anlayış için teşekkür eder, her türlü soru ve bilgilendirme ihtiyacınızda müşteri temsilcilerimizin sizlere memnuniyetle destek vereceğini bilgilerinize sunarız.</p>
            
            <p>Saygılarımızla,</p>

            <p>Arı Finansal Kiralama A.Ş.</p>
        '''

        def send_outlook_email(subject, message, from_email, recipient_list, attachments=None):
            email = EmailMultiAlternatives(
                subject,
                message,
                from_email,
                recipient_list,
            )
            email.attach_alternative(message, "text/html")
            if attachments:
                for attachment in attachments:
                    email.attach(attachment['name'], attachment['content'], attachment['mimetype'])
            email.send(fail_silently=False)
            #send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                
        subject = 'Kredi Kartı ile Yapılacak Ödemelere İlişkin Bilgilendirme'
        
        from_email = 'Arı Leasing <noreply@arileasing.com.tr>'
        recipient_list = email_list

        send_outlook_email(subject, message, from_email, recipient_list)

        print("done!")