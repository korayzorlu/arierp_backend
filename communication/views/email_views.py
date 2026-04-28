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

from communication.models import SMS, Email
from communication.utils.sms_utils import send_sms_with_turatel,check_sms_status
from communication.utils.email_utils import send_email_with_setrow,check_last_email
from communication.tasks import send_email_with_setrow_task
from partners.models import Partner
from risk.utils.common_utils import partners_for_project,template_for_risk_status,leases_for_project
from leasing.utils.common_utils import format_currency_tr,project_text

import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime,date,timedelta

class SendRiskEmailView(LoginRequiredMixin,View):
    model = Email

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)

        active_company_uuid = data.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        company_id = active_company.company.uuid
        
        # partners = partners_for_project(data)

        # recepients = []

        # for partner in partners:
        #     if partner.email and partner.email != "":
        #         leases = leases_for_project({**data, "partner_id": partner.uuid})
            
        #         if leases:
        #             for lease in leases:
        #                 if lease.contract:
        #                     if not check_last_email(partner.email):
        #                         recepients.append(
        #                             {
        #                                 "email": partner.email,
        #                                 "variables": {
        #                                     "konu": data.get("subject"),
        #                                     "proje": project_text(data),
        #                                     "sozlesme": lease.contract.code if lease.contract else "",
        #                                     "tutar": format_currency_tr(lease.overdue_amount)
        #                                 }
        #                             }
        #                         )

        #test
        recipients = [
            {
                "email": "korayzorllu@gmail.com",
                "variables": {
                    "konu": "Ödeme Hatırlatma Bilgilendirmesi",
                    "proje": "Sinpaş Kızılbük",
                    "sozlesme": "67985",
                    "tutar": "156.897,00"
                }
            },
            {
                "email": "korayzorllu@gmail.com",
                "variables": {
                    "konu": "Ödeme Hatırlatma Bilgilendirmesi",
                    "proje": "Sinpaş Kızılbük",
                    "sozlesme": "67593/1",
                    "tutar": "75.600,00"
                }
            }
        ]

        # recipients = []

        # for recipient in recipientss:
        #     if check_last_email(recipient.get("email")):
        #         return JsonResponse({'message': 'Son bir saat içerisinde aynı e-posta adresine bir mesaj gönderilmiştir. Lütfen daha sonra tekrar deneyiniz.','status':'error'}, status=400)
        #     recipients.append(
        #         {
        #             "email": recipient.get("email"),
        #             "variables": {
        #                 "konu": recipient.get("variables", {}).get("konu"),
        #                 "proje": recipient.get("variables", {}).get("proje"),
        #                 "sozlesme": recipient.get("variables", {}).get("sozlesme"),
        #                 "tutar": recipient.get("variables", {}).get("tutar")
        #             }
        #         }
        #     )
        #test-end
        
        params = {
            "user_id": str(request.user.uuid),
            "company_id": str(company_id),
            "recipients": recipients,
            "template": template_for_risk_status(data.get("risk_status"))
        }

        send_email_with_setrow_task.delay(params)

        return JsonResponse({'message': 'E-posta gönderimi başlatıldı. Mesajların iletim durumunu iletişim sütununda yer alan mesaj butonlarından takip edebilirsiniz.','status':'success'}, status=200)
    
