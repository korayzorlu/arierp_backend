from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.utils import timezone

from .turatel_utils import send_turatel_sms,get_turatel_status
from communication.models import SMS
from partners.models import Partner
from leasing.models import Lease
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr



def send_sms_with_turatel(params):
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        Q(partner_contracts__contract_leases__is_credit=False) &
        Q(partner_contracts__contract_leases__is_under_review=False) &
        Q(partner_contracts__contract_warning_notices__isnull=True) &
        Q(partner_contracts__contract_leases__overdue_days__gt=0) &
        Q(partner_contracts__contract_leases__overdue_days__lte=30) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=100)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )

    create_objs = []
    data = {"messageText" : "[##MesajMetni##]", "receiverList" : [], "personalMessages" : []}
    for obj in objs:
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(params) &
            Q(contract__partner = obj) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=30) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).order_by("-overdue_amount").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )
        
        total_overdue_amount = 0
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount

            SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi aşağıda linki bulunan online sistemden kontrol edip ödeme yapabilirsiniz." if params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. {"https://odeme.arileasing.com.tr/online-islemler//login.aspx  " if params.get('project') != 'sinpas' else ""}Arı Finansal Kiralama(İletişim: 02123102721 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
            SMS_TEXT_TEST = "Bu bir test mesajıdır. Lütfen dikkate almayınız."

            data["personalMessages"].append({
                "parameter": [
                    SMS_TEXT,
                ]
            })
            data["receiverList"].append(obj.phone_number)

        # create_objs.append(SMS(
        #     company = obj.company,
        #     partner = obj,
        #     category = 'risk',
        #     send_date = timezone.now(),
        #     text = SMS_TEXT,
        #     phone_number = obj.phone_number,
        # ))

    turatel_response = send_turatel_sms(data)

    sms_result = turatel_response.get("message", {}).get("sendSmsResult", {})
    package_result = get_turatel_status({"packetId": sms_result.get("PacketId", "")}).get("message", {}).get("data", {}).get("messageStatusList", {})

    print(sms_result)
    print("-------------------")
    print(package_result)
    
    for message_id in sms_result.get("MessageIdList", {}).get("MessageId", []):
        
        if message_id != "-19":
            pass
    
    return len(objs)