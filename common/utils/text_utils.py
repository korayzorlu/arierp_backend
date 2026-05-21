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
        if list == "tapu_almayanlar":
            return f"Test mesajıdır, lütfen dikkate almayınız. Arı Finansal Kiralama(İletişim: 4447680 / rig@arileasing.com.tr)Mernis No: 0147005285500018"

