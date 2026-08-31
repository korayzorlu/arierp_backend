from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.http import JsonResponse
from django.utils.timezone import now,localtime

from .models import WhatsappMessage, RealEstateAgent
from common.utils.common_utils import transform_phone_number,parse_amount,format_currency_tr,round_thousand,round_hundred

import requests
from decimal import Decimal
from datetime import datetime,date,timedelta

TURKISH_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

def format_date_tr(d):
    return f"{d.day:02d} {TURKISH_MONTHS[d.month]} {d.year}"

def pmt(rate, nper, pv):
    if rate == 0:
        return pv / nper
    return (rate * pv) / (1 - (1 + rate) ** -nper)

def sum_stepped_series(first, annual_growth_percent, months):
    growth = annual_growth_percent / 100
    full_years = months // 12
    remainder_months = months % 12
    years_sum = full_years if growth == 0 else ( (1 + growth) ** full_years - 1) / growth
    remainder_contribution = remainder_months * (1 + growth) ** full_years
    return first * (12 * years_sum + remainder_contribution)

def transform_emlak_amounts(amount):
    vat_rate = Decimal("16.50")
    tufe = Decimal("7")
    enflasyon = Decimal("25.00")
    price = amount
    down_payment = price * Decimal("0.30")
    vade = 120

    annual_rate_decimal = tufe / 100
    vat_decimal = vat_rate / 100
    loan_amount = price - down_payment
    monthlyRate = (1 + annual_rate_decimal) ** (Decimal("1.00") / Decimal("12.00")) - 1
    seller_first_rent = pmt(monthlyRate, vade, loan_amount)
    real_total = down_payment + seller_first_rent * vade
    nominal_total = down_payment + sum_stepped_series(seller_first_rent, enflasyon, vade)
    return {
        "pesinat" : down_payment,
        "kredi_tutari": loan_amount,
        "aylik_tufe_orani": monthlyRate * 100,
        "leasing_orani": vat_rate,
        "satici_ilk_kira": seller_first_rent,
        "alici_ilk_kira_kdv_dahil": seller_first_rent * (1 + vat_decimal),
        "alici_pesinat_kdv_dahil": down_payment * (1 + vat_decimal),
        "reel_satis_tutari": real_total,
        "nominal_satis_tutari": nominal_total
    }

def make_whatsapp_message(data):
    phone_number_1 = transform_phone_number(data.get("phone_number_1"))
    #phone_number_2 = transform_phone_number(data.get("phone_number_2"))

    if RealEstateAgent.objects.filter(company = data.get("company"), name = data.get("name"), phone_number_1 = phone_number_1).exists():
        real_estate_agent = RealEstateAgent.objects.get(company = data.get("company"), name = data.get("name"), phone_number_1 = phone_number_1)
    else:
        real_estate_agent = RealEstateAgent.objects.create(
            company = data.get("company"),
            name = data.get("name"),
            phone_number_1 = phone_number_1,
            #phone_number_2 = phone_number_2
        )

    amount = parse_amount(data.get("amount"))

    emlak_data = transform_emlak_amounts(amount)

    meet_date = format_date_tr(datetime.strptime(data.get("meet_date"), "%Y-%m-%d").date()) if data.get("meet_date") else ""
    online_meet_date = format_date_tr(datetime.strptime(data.get("online_meet_date"), "%Y-%m-%d").date()) if data.get("online_meet_date") else ""
    
    text1 = f"""Sayın {data.get("name")},

İlanlarınızı ve kaliteli portföyünüzü inceledik. Satışlarınızı Sinpaş İştiraki Arı Finansal Kiralama ile hızlandırabilirsiniz. Müşteriniz gayrimenkulün asgari %30'unu peşin tahsil edip kalanını vadeler halinde alabilir. Böylece gayrimenkulü satarken TÜFE + %7 reel getiri sağlar. Arı Finansal Kiralama bu hizmetiniz için %1,5+KDV hizmet bedeli öder.

Sitenizde yer alan {data.get("ilan_no")} nolu ilana ilişkin olarak özet aşağıda verilmiştir.

1- {(format_currency_tr(round_thousand(amount)))} TL yerine TÜFE + %7 ile reel olarak {format_currency_tr(round_thousand(emlak_data.get("reel_satis_tutari")))} TL satabilirsiniz. TÜFE'nin ortalama %25 olduğu varsayımı ile 120 ay boyunca toplam {format_currency_tr(round_thousand(emlak_data.get("nominal_satis_tutari")))} TL satış geliri elde eder. Gayrimenkulü 5 yıldan fazla elinde bulunduran satıcı bundan gelir vergisi ve stopaj ödemez.

2- Gayrimenkulün satış bedelinin %30 olan {format_currency_tr(round_thousand(emlak_data.get("pesinat")))} TL peşin alır. Kalan tutarı 120 ay boyunca {format_currency_tr(round_hundred(emlak_data.get("satici_ilk_kira")))} TL olarak alır. Yıllık olarak TÜFE oranında artırılır. Satıcı peşinat oranını artırabilir veya vadeyi kısaltabilir.
    
3- Alıcı ise KDV dahil %16,5 eklenerek ödemelerini yapar. Peşinatı {format_currency_tr(round_thousand(emlak_data.get("alici_pesinat_kdv_dahil")))} TL ve taksitleri {format_currency_tr(round_hundred(emlak_data.get("alici_ilk_kira_kdv_dahil")))} TL olarak öder. Alıcı ile satıcı arasındaki fark %10 KDV ve Emlak Danışmanı Hizmet Bedeli olarak ödenmek üzere Arı Finansal Kiralamada kalır. 
    
4- Bu süreçte tarafların sözleşmesinin , tahsilatların, takibin ödemelerin yapılması süreçlerini 27 yıllık deneyimi ile Sinpaş İştiraki Arı Finansal Kiralama yürütür. 

{meet_date} tarihinde Sinpaş Holding Binasında (Beşiktaş) düzenleyeceğimiz özel bilgilendirme toplantısında sizleri de aramızda görmekten mutluluk duyarız.

    """
    text2 = f"""🏠 Satamadığınız portföyü satışa dönüştürmeye hazır mısınız?

Konut kredisine ulaşamayan müşterinize 120 aya kadar vade, satıcınıza yeni bir satış modeli, size ise mevcut komisyonunuza ek %1,5 + KDV satış primi.
Arı Leasing Gayrimenkul Satış Modelini gerçek rakamlarla anlatacağımız özel toplantımıza davetlisiniz.

📅 1 Eylül 2026 Salı
⏰ 10:00 – 11:00
📍 Sinpaş Plaza – Beşiktaş

Krediler kapalı. Ama satışın yolu açık.

👉 Katılım için KATILIYORUM yazmanız yeterli.

Arı Leasing | Sinpaş Grubu iştiraki
    """

    text = f"""Sayın {data.get("name")},

Kat mülkiyetli konutları Finansal Kiralama ile satabilirsiniz. Böylece mevcut komisyonunuza ek %2+kdv satış primi alırsınız. Modeli gerçek rakamlarla anlatıyoruz, toplantımıza davetlisiniz.

{meet_date} --> Sinpaş Plaza, Konferans Salonu

{online_meet_date} --> Microsoft Teams - Çevrimiçi

Toplantıya kayıt için lütfen aşağıdaki bağlantıya tıklayın:
[Kayıt Linki](https://forms.cloud.microsoft/r/R1QS6mMqJF)

Arı Leasing | Sinpaş Grubu iştiraki
    """

    wp_message = WhatsappMessage.objects.create(
        company = data.get("company"),
        real_estate_agent = real_estate_agent,
        ilan_no = data.get("ilan_no"),
        amount = amount,
        text = text,
    )

    response = requests.post(
        "https://emlak.arileasing.com.tr/api/whatsapp/ingest/",
        headers={"X-Api-Key": settings.EMLAK_WHATSAPP_INGEST_API_KEY},
        json={"phone_number": wp_message.real_estate_agent.phone_number_1, "message": wp_message.text},
    )

    print(response)

    


def is_valid_whatsapp_message_data(data):
    parameters = [
        "company",
        "name",
        "phone_number_1",
        "phone_number_2",
        "ilan_no",
        "amount",
        "meet_date",
        "online_meet_date",
    ]

    unknown_keys = set(data.keys()) - set(parameters)

    #zorunlu parametrelerin kontrolü
    if unknown_keys:
        return False, JsonResponse({'message': f'Geçersiz parametre(ler): {", ".join(sorted(unknown_keys))}', 'status': 'error'}, status=400)
    
    if not data.get('name') or data.get('name').strip() == "":
        return False, JsonResponse({'message': 'Emlakçı ismi eksik!','status':'error'}, status=400)

    if not data.get('phone_number_1') or data.get('phone_number_1').strip() == "":
         return False, JsonResponse({'message': 'Emlakçı telefonu eksik!','status':'error'}, status=400)

    if not data.get('ilan_no') or data.get('ilan_no').strip() == "":
        return False, JsonResponse({'message': 'İlan no eksik!','status':'error'}, status=400)

    if not data.get('amount') or data.get('amount').strip() == "":
        return False, JsonResponse({'message': 'İlan tutarı eksik!','status':'error'}, status=400)

    if not data.get('meet_date') or data.get('meet_date').strip() == "":
        return False, JsonResponse({'message': 'Toplantı tarihi eksik!','status':'error'}, status=400)

    if not data.get('online_meet_date') or data.get('online_meet_date').strip() == "":
        return False, JsonResponse({'message': 'Çevrimiçi toplantı tarihi eksik!','status':'error'}, status=400)

    return True, None