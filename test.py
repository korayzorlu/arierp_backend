# from decimal import Decimal, ROUND_HALF_UP
# from leasing.models import Lease,Installment
import requests
from datetime import datetime,timedelta

import os
import pandas as pd
import json

# installments = Installment.objects.select_related("lease").all()
# installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency}
# obj = (installment_by_code.get(("91556",0)))

# print(obj)


# url = 'http://localhost:8000/api/leasing/kizilbuk_risk_partners/?ac=899bc2f0-17d9-4067-a2a2-231b92bb9e59&format=datatables'

# response = requests.get(url).json()
# print(response)

# Aranacak kelime
# aranan_kelime = " depo "  # Buraya aramak istediğin kelimeyi yaz

# # Excel dosyalarının bulunduğu klasör yolu
# klasor_yolu = "/mnt/c/Users/koray.zorlu/Desktop/BANKA BAKİYE MUTABAKAT/BANKA BAKİYE MUTABAKAT 2025" 

# # Sonuçları tutacak liste
# bulunan_satirlar = []

# for dosya_adi in os.listdir(klasor_yolu):
#     if dosya_adi.endswith(".xlsx") or dosya_adi.endswith(".xls"):
#         dosya_yolu = os.path.join(klasor_yolu, dosya_adi)
#         print(f"Taranıyor: {dosya_adi}")

#         try:
#             # Dosyadaki tüm sayfaları oku
#             excel = pd.ExcelFile(dosya_yolu)
#             for sayfa in excel.sheet_names:
#                 df = pd.read_excel(dosya_yolu, sheet_name=sayfa)

#                 # Tüm hücreleri string'e çevir
#                 df_str = df.astype(str)

#                 # Kelimenin geçtiği satırları bul
#                 mask = df_str.apply(lambda x: x.str.contains(aranan_kelime, case=False, na=False)).any(axis=1)
#                 eslesen_satirlar = df[mask]

#                 # Bulunan satırları listeye ekle (dosya adı ve sayfa adıyla birlikte)
#                 for _, satir in eslesen_satirlar.iterrows():
#                     bulunan_satirlar.append({
#                         "dosya": dosya_adi,
#                         "sayfa": sayfa,
#                         "satir": satir.to_dict()
#                     })
#         except Exception as e:
#             print(f"Hata oluştu: {dosya_adi} -> {e}")

# print(f"\nToplam bulunan satır sayısı: {len(bulunan_satirlar)}")

# # Bulunan satırları ayrı bir Excel dosyasına kaydet
# if bulunan_satirlar:
#     pd.DataFrame(bulunan_satirlar).to_excel("bulunan_satirlar.xlsx", index=False)
#     print("\n📁 'bulunan_satirlar.xlsx' dosyasına kaydedildi.")
# else:
#     print("\nHiç eşleşme bulunamadı.")



import xml.etree.ElementTree as ET

url = "https://www.tcmb.gov.tr/kurlar/202509/11092025.xml"  # örnek TCMB yolu
response = requests.get(url)

# XML verisini parse et
# XML verisini parse et
root = ET.fromstring(response.content)

currencies = []
for currency in root.findall("Currency"):
    data = {
        "CrossOrder": currency.get("CrossOrder"),
        "Kod": currency.get("Kod"),
        "CurrencyCode": currency.get("CurrencyCode"),
        "Unit": currency.findtext("Unit"),
        "Isim": currency.findtext("Isim"),
        "CurrencyName": currency.findtext("CurrencyName"),
        "ForexBuying": currency.findtext("ForexBuying"),
        "ForexSelling": currency.findtext("ForexSelling"),
        "BanknoteBuying": currency.findtext("BanknoteBuying"),
        "BanknoteSelling": currency.findtext("BanknoteSelling"),
        "CrossRateUSD": currency.findtext("CrossRateUSD"),
        "CrossRateOther": currency.findtext("CrossRateOther"),
    }
    currencies.append(data)

data_json = json.dumps(currencies, ensure_ascii=False, indent=2)

result = next((item for item in currencies if item["Kod"] == "USD"), None)
print(result)


