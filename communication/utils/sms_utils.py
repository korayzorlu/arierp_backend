from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.utils import timezone

from datetime import datetime,date,timedelta
import logging
import traceback
import time

from .turatel_utils import send_turatel_sms,get_turatel_status_with_package,get_turatel_status_with_message
from communication.models import SMS
from partners.models import Partner
from leasing.models import Lease
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from risk.utils.common_utils import partners_for_project,leases_for_project
from companies.models import Company,UserCompany
from common.utils.text_utils import get_sms_text

def sms_text_for_risk_status(params,contracts,total_overdue_amount,overdue_start_date):
    tomorrow = date.today() + timedelta(days=1)
    contract_label = "sözleşmenize" if len(contracts) == 1 else "sözleşmelerinize"
    if params.get("risk_status") == "risk_partners":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "to_warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksiti bulunmaktadır. Bugün itibari ile ihtarname süreci başlatılmıştır. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesi’ne ait {overdue_start_date.strftime("%d.%m.%Y")} son ödeme tarihli {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:4447680 Mernis No:0147005285500018"
    elif params.get("risk_status") == "to_terminated":
        SMS_TEXT = F"Değerli müşterimiz, {', '.join(contracts)} No.lu {contract_label} ilişkin {format_currency_tr(total_overdue_amount)} TL borcunuz bulunmaktadır. {date.today().strftime('%d.%m.%Y')} tarihi itibarıyla sonlandırılacağını üzülerek bilgilerinize sunarız. Herhangi bir sorunuz olması halinde bizimle 4447680 no.lu telefondan ulaşabilirsiniz. Arı Finansal Kiralama Mersis No: 0147005285500018"
    elif params.get("risk_status") == "today_partners":
        SMS_TEXT = F"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin ödemelerini hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "tomorrow_partners":
        SMS_TEXT = F"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {tomorrow.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "global_notification":
        SMS_TEXT = F"Değerli müşterimiz, Ödemelerinizin gecikmesiz işlenebilmesi için Eft/Havale işlemlerinizde açıklama kısmına mutlaka sözleşme numaranızı,sözleşme sahibi T.C. numarasını ve sözleşme sahibi isim-soy isim bilgisini yazmanız gerekmektedir. IBAN: TR27 0001 2009 6260 0010 1009 81 Alıcı Adı: Arı Finansal Kiralama Arı Finansal Kiralama. Mernis No: 0147005285500018"
    return SMS_TEXT or ""


def send_turatel_sms_for_check(params):
    tomorrow = date.today() + timedelta(days=1)
    if params.get("risk_status") == "risk_partners":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin 50.000,00 TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "to_warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin 50.000,00 TL ödenmemiş taksiti bulunmaktadır. Bugün itibari ile ihtarname süreci başlatılmıştır. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "warned":
        SMS_TEXT = f"Değerli müşterimiz, {project_text(params)} projesi’ne ait 01.01.2026 son ödeme tarihli 50.000,00 TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:4447680 Mernis No:0147005285500018"
    elif params.get("risk_status") == "to_terminated":
        SMS_TEXT = F"Değerli müşterimiz, 99999 No.lu sözleşmenize ilişkin 50.000,00 TL TL borcunuz bulunmaktadır. {date.today().strftime('%d.%m.%Y')} tarihi itibarıyla sonlandırılacağını üzülerek bilgilerinize sunarız. Herhangi bir sorunuz olması halinde bizimle 4447680 no.lu telefondan ulaşabilirsiniz. Arı Finansal Kiralama Mersis No: 0147005285500018"
    elif params.get("risk_status") == "today_partners":
        SMS_TEXT = F"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin ödemelerini hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "tomorrow_partners":
        SMS_TEXT = F"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {tomorrow.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
    elif params.get("risk_status") == "global_notification":
        SMS_TEXT = F"Değerli müşterimiz, Ödemelerinizin gecikmesiz işlenebilmesi için Eft/Havale işlemlerinizde açıklama kısmına mutlaka sözleşme numaranızı,sözleşme sahibi T.C. numarasını ve sözleşme sahibi isim-soy isim bilgisini yazmanız gerekmektedir. IBAN: TR27 0001 2009 6260 0010 1009 81 Alıcı Adı: Arı Finansal Kiralama Arı Finansal Kiralama. Mernis No: 0147005285500018"

    data = {
        "messageText" : SMS_TEXT,
        "receiverList" : ["05357750255","05332260858","05456227095","05548919220"],
    }

    send_turatel_sms(data)

def send_sms_with_turatel(params):
    objs = partners_for_project(params)

    create_objs = []
    message_id_list = []
    
    send_turatel_sms_for_check(params)
    
    try:
        for obj in objs:
            if obj.tc_vkn_no in ["35263659368","35236660292","35227660584","35221660702","20416138364","14615595400"]:
                continue

            leases = leases_for_project({**params, "partner_id": obj.uuid})
            
            total_overdue_amount = 0
            max_overdue_days = 0
            if leases:
                contracts = []
                for lease in leases:
                    total_overdue_amount += lease.overdue_amount
                    if lease.overdue_days > max_overdue_days:
                        max_overdue_days = lease.overdue_days
                    contracts.append(lease.contract.code)
                if max_overdue_days > 0:
                    overdue_start_date = date.today() - timedelta(days=max_overdue_days)

                SMS_TEXT = sms_text_for_risk_status(params,contracts,total_overdue_amount,overdue_start_date)
                
                data = {
                    "messageText" : SMS_TEXT,
                    "receiverList" : [obj.phone_number],
                }

            if not obj.partner_smss.filter(delivery_date__date=timezone.localdate(),status__in=["1","2"]).exists():
               
                now = timezone.now()
                turatel_response = send_turatel_sms(data)

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

def send_sms_on_command(company):
    company = Company.objects.filter(id=int(company)).first()

    SMS_TEXT = "Değerli Müşterimiz, KEP adresiniz üzerinden paylaşılan Müşteri Bilgi Formumuzun tarafımıza iletilmesi konusunda değerli desteklerinizi rica ederiz. Mersis: 0147005285500018"

    receiver_list = ["5542663970","5386780304","5051706822", "5052132149", "5052622273", "5052724250", "5053002204", "5053397860", "5053949437", "5055156903", "5055244184", "5055863825", "5056236895", "5056361090", "5058245254", "5058264493", "5058296861", "5059382928", "5061152438", "5062394529", "5065450560", "5065783829", "5066034217", "5069783783", "5071563708", "5071939507", "5073119676", "5073576777", "5073875167", "5075271023", "5077338995", "5077399449", "5077559568", "5078158416", "5079000996", "5300476981", "5302919172", "5303150046", "5303279452", "5303868994", "5304427891", "5304586718", "5304691141", "5304979793", "5305043993", "5305482430", "5306060631", "5306067009", "5306374169", "5306417549", "5306804197", "5306891303", "5309728523", "5312316727", "5317426583", "5320590590", "5320666859", "5320693490", "5321586250", "5321696699", "5322049999", "5322057550", "5322066964", "5322088074", "5322101576", "5322135264", "5322205622", "5322265151", "5322335552", "5322448845", "5322474400", "5322537799", "5322716918", "5322853693", "5322917231", "5322962294", "5323016685", "5323033537", "5323115944", "5323138343", "5323184342", "5323234167", "5323263230", "5323411150", "5323430579", "5323461804", "5323503932", "5323711744", "5323866666", "5323928696", "5323942123", "5324008968", "5324131052", "5324137267", "5324212954", "5324223873", "5324409097", "5324512849", "5324563736", "5324628675", "5324677050", "5324818755", "5324871976", "5325005101", "5325016423", "5325063216", "5325169682", "5325258851", "5325497193", "5325569368", "5325596228", "5325690446", "5325724463", "5325768259", "5325769351", "5325821749", "5325888207", "5325966044", "5326033691", "5326138958", "5326171656", "5326299539", "5326405364", "5326450517", "5326452785", "5326748133", "5326760904", "5326834124", "5326857948", "5326932733", "5326988223", "5327021200", "5327082121", "5327115579", "5327178075", "5327220076", "5327246150", "5327373888", "5327393959", "5327773550", "5327787921", "5327789479", "5327907220", "5327963662", "5331631391", "5332109054", "5332125345", "5332158015", "5332171951", "5332232100", "5332411964", "5332506363", "5332922028", "5333061048", "5333327880", "5333548024", "5333686191", "5333726040", "5333727831", "5333785678", "5333896351", "5334115363", "5334355171", "5334658263", "5334685704", "5335030333", "5335681253", "5335748581", "5335937390", "5336183479", "5336307153", "5336402825", "5336473843", "5336485213", "5336573333", "5336838643", "5337259801", "5337391171", "5337758454", "5338138258", "5339357735", "5343657150", "5344757444", "5345154676", "5345534182", "5345641629", "5345976479", "5345991453", "5348243898", "5350864095", "5352551400", "5353780146", "5354211876", "5355506499", "5355622842", "5355659580", "5355919696", "5357608872", "5358106451", "5359201277", "5359314444", "5359363934", "5359506383", "5359708780", "5359892883", "5363124829", "5363493622", "5363625396", "5364769916", "5365023343", "5369463019", "5369898904", "5372302384", "5372550234", "5374323523", "5374759555", "5377802574", "5377923710", "5382559543", "5388697962", "5389692619", "5393025689", "5396210136", "5398457891", "5402121208", "5411310204", "5413102020", "5414133872", "5414275758", "5415063204", "5416434900", "5418501075", "5422104910", "5422165388", "5422310589", "5422403800", "5422507552", "5422655580", "5423219596", "5423437922", "5423973434", "5424154545", "5424270167", "5424519173", "5424869585", "5428983434", "5436195101", "5436756616", "5437656743", "5438797948", "5442722521", "5443471144", "5444969474", "5445231716", "5449225932", "5452603406", "5452750969", "5455344453", "5458041588", "5458202000", "5464342424", "5465525077", "5465601961", "5469790224", "5495456060", "5511232055", "5511720523", "5521854046", "5532358128", "5532684553", "5536327587", "5537998510", "5538763806", "5541540712", "5543021257", "5543323845", "5545662320", "5546401866", "5546554539", "5546654611", "5546813511", "5548027288", "5548322820", "5548815500", "5548865706", "5552552021", "5552552868", "5555217768", "5555306225", "5558228585", "5558760585", "5559819221", "5559937803", "5386780304"]
    
    for receiver in receiver_list:
        time.sleep(0.5)
        data = {
            "messageText" : SMS_TEXT,
            "receiverList" : [receiver],
        }

        now = timezone.now()
        turatel_response = send_turatel_sms(data)

        sms_result = turatel_response.get("message", {}).get("sendSmsResult", {})

        if sms_result.get("ErrorCode", "") != "0":
            return {"message_id_list": []}
        
        create_objs = []
        message_id_list = []
        if sms_result.get("MessageIdList", {}).get("MessageId", "") != "-19":
            sms_status = get_turatel_status_with_message({"messageIdList": [sms_result.get("MessageIdList", {}).get("MessageId", "")]})
            message_result = sms_status.get("message", {}).get("data", {}).get("messageStatusList", {})[0] if sms_status.get("message", {}) else None
            
            if message_result and str(sms_result.get("MessageIdList", {}).get("MessageId", "")) == str(message_result.get("messageId", "")):
                
                create_objs.append(SMS(
                    company = company,
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

def send_sms_util(params):
    active_company = UserCompany.objects.filter(uuid=params.get('activeCompany'), is_active=True).first()
    company = active_company.company if active_company else None

    SMS_TEXT = params.get('text', '')

    receiver_list = params.get('receiver_list', [])
    
    for receiver in receiver_list:
        time.sleep(0.1)
        sms_data = get_sms_text(app=params.get('app', ''), list=params.get('list', ''), params=receiver)
        data = {
            "messageText" : sms_data.get('text', ''),
            "receiverList" : [sms_data.get('phone_number', '')],
        }

        # print(data)
        # print("-----------------------------")

        now = timezone.now()
        turatel_response = send_turatel_sms(data)

        sms_result = turatel_response.get("message", {}).get("sendSmsResult", {})

        if sms_result.get("ErrorCode", "") != "0":
            return {"message_id_list": []}
        
        create_objs = []
        message_id_list = []
        if sms_result.get("MessageIdList", {}).get("MessageId", "") != "-19":
            sms_status = get_turatel_status_with_message({"messageIdList": [sms_result.get("MessageIdList", {}).get("MessageId", "")]})
            message_result = sms_status.get("message", {}).get("data", {}).get("messageStatusList", {})[0] if sms_status.get("message", {}) else None
            
            if message_result and str(sms_result.get("MessageIdList", {}).get("MessageId", "")) == str(message_result.get("messageId", "")):
                
                create_objs.append(SMS(
                    company = company,
                    packet_id = str(message_result.get("packetId", "")),
                    message_id = str(message_result.get("messageId", "")),
                    error_code = sms_result.get("ErrorCode", ""),
                    size = sms_result.get("messageSize", ""),
                    status = message_result.get("status", ""),
                    reason = message_result.get("reason", ""),
                    category = 'untitle_deed',
                    send_date = now,
                    delivery_date = now,
                    text = sms_data.get('text', ''),
                    phone_number = message_result.get("receiver", ""),
                ))
                message_id_list.append(str(message_result.get("messageId", "")))

        if create_objs:
            SMS.objects.bulk_create(create_objs)


