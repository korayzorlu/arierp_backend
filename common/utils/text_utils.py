from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr

from decimal import Decimal
from datetime import date,datetime,timedelta

def get_sms_text(*args,**kwargs):
    app = kwargs.get('app')
    list = kwargs.get('list')
    params = kwargs.get('params', {})

    if app == "risk":
        if list == "gecikmede":
            return f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(params.get('total_overdue_amount',Decimal('0.00')))} TL ödenmemiş taksiti bulunmaktadır. Bugün ödenmesi hususunda gereğini rica ederiz. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
        elif list == "ihtar_cekilecek":
            return f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {format_currency_tr(params.get('total_overdue_amount',Decimal('0.00')))} TL ödenmemiş taksiti bulunmaktadır. Bugün itibari ile ihtarname süreci başlatılmıştır. {"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
        elif list == "ihtar_cekilen":
            return f"Değerli müşterimiz, {project_text(params)} projesi’ne ait {params.get('overdue_start_date').strftime("%d.%m.%Y")} son ödeme tarihli {format_currency_tr(params.get('total_overdue_amount',Decimal('0.00')))} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:4447680 Mernis No:0147005285500018"
        elif list == "fesih_edilecek":
            return f"Değerli müşterimiz, {', '.join(params.get('contracts', []))} No.lu {params.get('contract_label')} ilişkin {format_currency_tr(params.get('total_overdue_amount',Decimal('0.00')))} TL borcunuz bulunmaktadır. {params.get('date', date.today()).strftime('%d.%m.%Y')} tarihi itibarıyla sonlandırılacağını üzülerek bilgilerinize sunarız. Herhangi bir sorunuz olması halinde bizimle 4447680 no.lu telefondan ulaşabilirsiniz. Arı Finansal Kiralama Mersis No: 0147005285500018"
        elif list == "bugun_odenecek":
            f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin ödemelerini hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"
        elif list == "yarin_odenecek":
            f"Değerli müşterimiz, {project_text(params)} projesinde bulunan sözleşmelerinizin {(date.today() + timedelta(days=1)).strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatmak isteriz.{"Ödemelerinizi online sistemden kontrol edip ödeme yapabilirsiniz. " if params.get('project') == 'kizilbuk' or params.get('project') =='kasaba' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama(İletişim: 4447680/rig@arileasing.com.tr)Mernis No: 0147005285500018"

    elif app == "operation":
        if list == "untitle_deed_leases":
            return {
                "text": f"Değerli müşterimiz , Sinpaş  projesine ait sözleşmenizin devir bedeli toplam {params.get('remaining_amount', Decimal('0.00'))} {'TL' if params.get('currency', 'TRY') == 'TRY' else params.get('currency', 'TL')} gecikmede olup, Arı Finansal Kiralamanın ilgili BANKA hesaplarına DEVİR BEDELİ açıklaması ile ödeme yapılmasını rica ederiz. ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. Arı Finansal Kiralama Mersis No.0147005285500018",
                "phone_number": params.get('contract__partner__phone_number', '')
            }

def get_email_template(*args,**kwargs):
    app = kwargs.get('app')
    list = kwargs.get('list')

    if app == "risk":
        if list == "risk_partners":
            return "b84e83786dbcbc132b0b25d293890ba6506ff7d0b474b2aa4e"
        elif list == "to_warned":
            return "c08c6a4b2932d6bdfab0a892b3e74c6109efee6f0d3d9d3c6b"
        elif list == "warned":
            return "a1a4c7f4501d25043d68e5d9bf10f44e8b59b06b1f43a9897a"
        elif list == "to_terminated":
            return "7cf3da7a1e8445d68939c3f30f5d181897931bf79e31c75201"
        elif list == "today_partners":
            return ""
        elif list == "tomorrow_partners":
            return ""
    elif app == "operation":
        if list == "untitle_deed_leases":
            return {
                "template": "a3226e38af372a4d29557a56ae657d20b6d4643ce912bf5957",
                "subject": "Ödeme Hatırlatma Bilgilendirmesi",
                "email_field": "contract__partner__email"
            }