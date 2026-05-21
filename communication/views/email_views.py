import uuid

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
from communication.tasks import send_email_with_setrow_task,send_email_global_with_setrow_task
from partners.models import Partner
from risk.utils.common_utils import partners_for_project,template_for_risk_status,leases_for_project
from leasing.utils.common_utils import format_currency_tr,project_text
from leasing.models import Lease
from common.utils.common_utils import get_emails_from_queryset


import os
import json
import pandas as pd
from decimal import Decimal
from datetime import datetime,date,timedelta

class SendEmailView(LoginRequiredMixin,View):
    model = Email

    def post(self, request, *args, **kwargs):
        from operation.api.views import UntitleDeedLeaseList
        from rest_framework.request import Request
        data = json.loads(request.body)
        
        # if request.user.authorization.department != 'operasyonn':
        #     return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)

        receiver_list, text = get_emails_from_queryset(request=request,data=data)

        test_receiver_list = [
            {
                "email": 'korayzorllu@gmail.com',
                "variables": {
                    "konu": 'Ödeme Hatırlatma Bilgilendirmesi - Test Maili',
                    "proje": project_text({"project": "kizilbuk"}),
                    "sozlesme": '99999',
                    "tutar": format_currency_tr(Decimal('0.00')),
                    "tarih": date.today().strftime('%d.%m.%Y')
                }
            },
        ]

        params = {
            "activeCompany": str(data.get("activeCompany")),
            "user_id": str(request.user.uuid),
            #"recipients": [{"email": item,"variables": {}} for item in receiver_list if item],
            "recipients": test_receiver_list,
            "template": template_for_risk_status(data.get("query"))
        }

        send_email_global_with_setrow_task.delay(params)        

        return JsonResponse({'message': 'Email gönderimi başlatıldı. Mesajların iletim durumunu iletişim sütununda yer alan mesaj butonlarından takip edebilirsiniz.','status':'success'}, status=200)

class SendRiskEmailView(LoginRequiredMixin,View):
    model = Email

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        
        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)

        active_company_uuid = data.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        company_id = active_company.company.uuid
        
        partners = partners_for_project(data)

        recipients = []

        ignore_tc_list = ["35263659368","35236660292","35227660584","35221660702","20416138364"]

        for partner in partners:
            if partner.email and partner.email != "" and partner.tc_vkn_no not in ignore_tc_list:
                leases = leases_for_project({**data, "partner_id": partner.uuid})
            
                if leases:
                    for lease in leases:
                        if lease.contract:
                            if not check_last_email(partner.email):
                                recipients.append(
                                    {
                                        "email": partner.email,
                                        "variables": {
                                            "konu": data.get("subject"),
                                            "proje": project_text(data),
                                            "sozlesme": lease.contract.code if lease.contract else "",
                                            "tutar": format_currency_tr(lease.overdue_amount),
                                            "tarih" : date.today().strftime('%d.%m.%Y')
                                        }
                                    }
                                )

        recipients.append(
            {
                "email": 'koray.zorlu@arileasing.com.tr',
                "variables": {
                    "konu": 'Ödeme Hatırlatma Bilgilendirmesi - Test Maili',
                    "proje": project_text(data),
                    "sozlesme": '99999',
                    "tutar": format_currency_tr(Decimal('0.00')),
                    "tarih": date.today().strftime('%d.%m.%Y')
                }
            },
            {
                "email": 'burcu.akgul@arileasing.com.tr',
                "variables": {
                    "konu": 'Ödeme Hatırlatma Bilgilendirmesi - Test Maili',
                    "proje": project_text(data),
                    "sozlesme": '99999',
                    "tutar": format_currency_tr(Decimal('0.00')),
                    "tarih": date.today().strftime('%d.%m.%Y')
                }
            }
        )

        #test
        # recipients = [
        #     {
        #         "email": "korayzorllu@gmail.com",
        #         "variables": {
        #             "konu": "Ödeme Hatırlatma Bilgilendirmesi",
        #             "proje": "Sinpaş Kızılbük",
        #             "sozlesme": "67985",
        #             "tutar": "156.897,00",
        #             "tarih" : date.today().strftime('%d.%m.%Y')
        #         }
        #     },
        #     {
        #         "email": "korayzorllu@gmail.com",
        #         "variables": {
        #             "konu": "Ödeme Hatırlatma Bilgilendirmesi",
        #             "proje": "Sinpaş Kızılbük",
        #             "sozlesme": "67593/1",
        #             "tutar": "75.600,00",
        #             "tarih" : date.today().strftime('%d.%m.%Y')
        #         }
        #     }
        # ]

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
        #                 "tutar": recipient.get("variables", {}).get("tutar"),
        #                 "tarih": recipient.get("variables", {}).get("tarih")
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
    
class SendRiskEmailSelectedView(LoginRequiredMixin,View):
    model = Email

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        uuids = data.get('uuids')
        
        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yoktur.','status':'error'}, status=403)

        active_company_uuid = data.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        company_id = active_company.company.uuid

        recipients = []
        ignore_tc_list = ["35263659368","35236660292","35227660584","35221660702","20416138364"]
    
        for uuid in uuids:
            lease = Lease.objects.select_related().filter(uuid = uuid).first()
            
            if lease:
                if lease.contract and lease.contract.partner and lease.contract.partner.email and lease.contract.partner.email != "" and lease.contract.partner.tc_vkn_no not in ignore_tc_list:

                    if not check_last_email(lease.contract.partner.email):
                        recipients.append(
                            {
                                "email": lease.contract.partner.email,
                                "variables": {
                                    "konu": data.get("subject"),
                                    "proje": project_text(data),
                                    "sozlesme": lease.contract.code if lease.contract else "",
                                    "tutar": format_currency_tr(lease.overdue_amount),
                                    "tarih" : date.today().strftime('%d.%m.%Y')
                                }
                            }
                        )

        recipients.append(
            {
                "email": 'koray.zorlu@arileasing.com.tr',
                "variables": {
                    "konu": 'Ödeme Hatırlatma Bilgilendirmesi - Test Maili',
                    "proje": project_text(data),
                    "sozlesme": '99999',
                    "tutar": format_currency_tr(Decimal('0.00')),
                    "tarih" : date.today().strftime('%d.%m.%Y')
                }
            },
            {
                "email": 'burcu.akgul@arileasing.com.tr',
                "variables": {
                    "konu": 'Ödeme Hatırlatma Bilgilendirmesi - Test Maili',
                    "proje": project_text(data),
                    "sozlesme": '99999',
                    "tutar": format_currency_tr(Decimal('0.00')),
                    "tarih": date.today().strftime('%d.%m.%Y')
                }
            }
        )

        #test
        # recipients = [
        #     {
        #         "email": "korayzorllu@gmail.com",
        #         "variables": {
        #             "konu": "Ödeme Hatırlatma Bilgilendirmesi",
        #             "proje": "Sinpaş Kızılbük",
        #             "sozlesme": "67985",
        #             "tutar": "156.897,00",
        #             "tarih" : date.today().strftime('%d.%m.%Y')
        #         }
        #     },
        #     {
        #         "email": "korayzorllu@gmail.com",
        #         "variables": {
        #             "konu": "Ödeme Hatırlatma Bilgilendirmesi",
        #             "proje": "Sinpaş Kızılbük",
        #             "sozlesme": "67593/1",
        #             "tutar": "75.600,00",
        #             "tarih" : date.today().strftime('%d.%m.%Y')
        #         }
        #     }
        # ]
        #test-end
        
        params = {
            "user_id": str(request.user.uuid),
            "company_id": str(company_id),
            "recipients": recipients,
            "template": template_for_risk_status(data.get("risk_status")),
            "template_name": data.get("template_name"),
        }

        send_email_with_setrow_task.delay(params)

        return JsonResponse({'message': 'E-posta gönderimi başlatıldı. Mesajların iletim durumunu iletişim sütununda yer alan mesaj butonlarından takip edebilirsiniz.','status':'success'}, status=200)


