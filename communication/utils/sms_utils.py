from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.utils import timezone

from datetime import datetime,date,timedelta
import logging
import traceback

from .turatel_utils import send_turatel_sms,get_turatel_status_with_package,get_turatel_status_with_message
from communication.models import SMS
from partners.models import Partner
from leasing.models import Lease
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from risk.utils.common_utils import partners_for_project,leases_for_project

def sms_text_for_risk_status(params,total_overdue_amount,overdue_start_date):
    if params.get("risk_status") == "risk_partners":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 02123102721/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "to_warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksiti bulunmaktadır. Bugün itibari ile ihtarname süreci başlatılmıştır. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 02123102721 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesi’ne ait {overdue_start_date.strftime("%d.%m.%Y")} son ödeme tarihli {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
    elif params.get("risk_status") == "to_terminated":
        SMS_TEXT = F"Değerli müşterimiz, {project_text(params)} projesi’ne ait {format_currency_tr(total_overdue_amount)} TL ihtar bakiyeniz bulunmaktadır. Fesih sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"

    return SMS_TEXT or ""


def send_turatel_sms_for_check(params):
    SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin 50.000,00 TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 02123102721/rig@arileasing.com.tr)Mernis No: 0147005285500018"

    data = {
        "messageText" : SMS_TEXT,
        "receiverList" : ["05357750255","05332260858","05456227095","05548919220","05413831801","05534565457"],
    }

    send_turatel_sms(data)

def send_sms_with_turatel(params):
    objs = partners_for_project(params)

    create_objs = []
    message_id_list = []
    
    send_turatel_sms_for_check(params)
    
    try:
        for obj in objs:
            leases = leases_for_project({**params, "partner_id": obj.uuid})
            
            total_overdue_amount = 0
            max_overdue_days = 0
            if leases:
                for lease in leases:
                    total_overdue_amount += lease.overdue_amount
                    if lease.overdue_days > max_overdue_days:
                        max_overdue_days = lease.overdue_days
                if max_overdue_days > 0:
                    overdue_start_date = date.today() - timedelta(days=max_overdue_days)

                SMS_TEXT = sms_text_for_risk_status(params,total_overdue_amount,overdue_start_date)
                
                data = {
                    "messageText" : SMS_TEXT,
                    "receiverList" : [obj.phone_number],
                }

            if not obj.partner_smss.filter(delivery_date__date=timezone.localdate(),status__in=["1","2"]).exists():
               
                now = timezone.now()
                turatel_response = send_turatel_sms(data)
                print(turatel_response)

                sms_result = turatel_response.get("message", {}).get("sendSmsResult", {})
                if sms_result.get("ErrorCode", "") != "0":
                    continue
                if sms_result.get("MessageIdList", {}).get("MessageId", "") != "-19":
                    sms_status = get_turatel_status_with_message({"messageIdList": [sms_result.get("MessageIdList", {}).get("MessageId", "")]})
                    message_result = sms_status.get("message", {}).get("data", {}).get("messageStatusList", {})[0] if sms_status.get("message", {}) else None
                    
                    if message_result and str(sms_result.get("MessageIdList", {}).get("MessageId", "")) == str(message_result.get("messageId", "")):
                        
                        create_objs.append(SMS(
                            company = obj.company,
                            partner = obj,
                            packet_id = str(message_result.get("packetId", "")),
                            message_id = str(message_result.get("messageId", "")),
                            error_code = sms_result.get("ErrorCode", ""),
                            size = sms_result.get("messageSize", ""),
                            status = message_result.get("status", ""),
                            reason = message_result.get("reason", ""),
                            category = 'risk',
                            send_date = now,
                            delivery_date = now,
                            text = SMS_TEXT,
                            phone_number = message_result.get("receiver", ""),
                        ))
                        message_id_list.append(str(message_result.get("messageId", "")))

        if create_objs:
            SMS.objects.bulk_create(create_objs)

        return {"message_id_list": message_id_list}
    except Exception as e:
        traceback.print_exc()
        return {"message_id_list": []}

def check_sms_status(params):
    messages = params.get("message_id_list", [])

    for message_id in messages:
        message_result = get_turatel_status_with_message({"messageIdList": [message_id]}).get("message", {}).get("data", {}).get("messageStatusList", [])
        print(message_result)
        if message_result:
            if str(message_result[0].get("messageId", "")) == message_id:
                sms_obj = SMS.objects.select_related().filter(message_id=message_id).first()
                if sms_obj:
                    sms_obj.status = message_result[0].get("status", "")
                    sms_obj.reason = message_result[0].get("reason", "")
                    delivery_date_str = message_result[0].get("deliveryDate", "")
                    if len(delivery_date_str) == 12:
                        sms_obj.delivery_date = datetime.strptime(delivery_date_str, "%d%m%y%H%M%S") if delivery_date_str else None
                    sms_obj.save()


