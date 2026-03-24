# VPos Transaction API — Endpoint Dokümantasyonu

## POST /api/finance/add_vpos_transaction/

Sanal POS üzerinden gerçekleşen ödeme işlemlerini sisteme kaydetmek için kullanılır.
Bu endpoint oturum gerektirmez; kimlik doğrulama `CompanyId` ve `ValidationKey` alanları üzerinden yapılır.

---

### Genel Bilgiler

| Özellik      | Değer                                |
|--------------|--------------------------------------|
| URL          | `/api/finance/add_vpos_transaction/` |
| Method       | `POST`                               |
| Content-Type | `application/json`                   |
| Auth         | Oturum gerekmez                      |

---

### Zorunlu Alanlar

| Alan                  | Tip      | Açıklama                                        |
|-----------------------|----------|-------------------------------------------------|
| `CompanyId`           | UUID     | İşlemin ilişkilendirileceği şirket UUID'si      |
| `ValidationKey`       | string   | Sunucu tarafında doğrulanan gizli anahtar       |
| `ProcessDate`         | dateTime | İşlem tarihi (ISO 8601, örn. `2024-01-15T10:30:00`) |
| `MusteriTipi`         | integer  | Müşteri tipi: `1` = Kurumsal, `2` = Bireysel   |
| `PaidAmount`          | decimal  | Ödenen tutar (sıfırdan büyük olmalı)            |
| `LeasePostingGroupId` | boolean  | Leasing posting grup ID                         |

---

### Opsiyonel Alanlar — Kurumsal Müşteri (`MusteriTipi=1`)

| Alan           | Tip    | Açıklama              |
|----------------|--------|-----------------------|
| `FirmaAdi`     | string | Firma adı             |
| `KurumTipi`    | string | Kurum tipi            |
| `VergiDairesi` | string | Vergi dairesi         |
| `VergiNo`      | string | Vergi numarası        |
| `WebSitesi`    | string | Web sitesi            |
| `Adres`        | string | Adres                 |
| `Ulke`         | string | Ülke                  |
| `Sehir`        | string | Şehir                 |
| `Ilce`         | string | İlçe                  |
| `Posta`        | string | Posta kodu            |
| `IletisimList` | array  | İletişim bilgileri (bkz. `Iletisim` nesnesi) |

**`IletisimList` eleman yapısı:**

| Alan              | Tip    | Açıklama                               |
|-------------------|--------|----------------------------------------|
| `IletisimTuru`    | string | İletişim türü (örn. `Telefon`, `Email`) |
| `IletisimDegeri`  | string | İletişim değeri                        |

```json
"IletisimList": [
  { "IletisimTuru": "Telefon", "IletisimDegeri": "+905001234567" },
  { "IletisimTuru": "Email",   "IletisimDegeri": "info@firma.com" }
]
```

---

### Opsiyonel Alanlar — Bireysel Müşteri (`MusteriTipi=2`)

| Alan                  | Tip    | Açıklama                    |
|-----------------------|--------|-----------------------------|
| `Ad`                  | string | Ad                          |
| `IkinciAd`            | string | İkinci ad                   |
| `OrtaAd`              | string | Orta ad                     |
| `SoyAd`               | string | Soyad                       |
| `Cinsiyet`            | string | Cinsiyet (`E` / `K`)        |
| `TCKimlikNo`          | string | TC kimlik numarası          |
| `PasaportNo`          | string | Pasaport numarası           |
| `Uyruk`               | string | Uyruk                       |
| `DogumTarih`          | date   | Doğum tarihi (`YYYY-MM-DD`) |
| `VergiDairesi_Birey`  | string | Vergi dairesi               |
| `VergiNo_Birey`       | string | Vergi numarası              |
| `Adres_Birey`         | string | Adres                       |
| `Ulke_Birey`          | string | Ülke                        |
| `Sehir_Birey`         | string | Şehir                       |
| `Ilce_Birey`          | string | İlçe                        |
| `Posta_Birey`         | string | Posta kodu                  |
| `IletisimList_Birey`  | array  | İletişim bilgileri (aynı `Iletisim` yapısı) |

---

### Opsiyonel Alanlar — Ortak

| Alan              | Tip    | Açıklama                        |
|-------------------|--------|---------------------------------|
| `UserName`        | string | Kullanıcı adı                   |
| `Password`        | string | Şifre                           |
| `Telefon`         | string | Telefon numarası                |
| `EMail`           | string | E-posta adresi                  |
| `Fax`             | string | Faks numarası                   |
| `BankCode`        | string | Banka kodu                      |
| `ContractCode`    | string | Sözleşme kodu                   |
| `CurrencyCode`    | string | Para birimi kodu (örn. `TRY`)   |
| `ExtTransactionId`| string | Harici işlem ID'si              |

---

### Başarılı Yanıt

**HTTP 200 OK**

```json
{
  "message": "Başarıyla kaydedildi!",
  "status": "success"
}
```

---

### Hata Yanıtları

Zorunlu alanlardan herhangi biri eksik, geçersiz veya beklenen formatta değilse `HTTP 400` döner. Yanıt yapısı:

```json
{
  "message": "Hata açıklaması (AlanAdi)",
  "status": "error"
}
```

---

### Örnek İstek (Python)

```python
import requests

url = "https://arinet.arileasing.com.tr/api/finance/add_vpos_transaction/"

payload = {
    # Zorunlu
    "CompanyId": "00000000-0000-0000-0000-000000000000",
    "ValidationKey": "your-validation-key",
    "ProcessDate": "2024-01-15T10:30:00",
    "MusteriTipi": 1,
    "PaidAmount": 1500.00,
    "LeasePostingGroupId": True,

    # Opsiyonel - Kurumsal
    "FirmaAdi": "Örnek Firma A.Ş.",
    "VergiNo": "1234567890",

    # Opsiyonel - Ortak
    "CurrencyCode": "TRY",
    "ExtTransactionId": "EXT-TX-001"
}

response = requests.post(url, json=payload)
print(response.status_code, response.json())
```

### Örnek İstek (cURL)

```bash
curl -X POST https://arinet.arileasing.com.tr/api/finance/add_vpos_transaction/ \
  -H "Content-Type: application/json" \
  -d '{
    "CompanyId": "00000000-0000-0000-0000-000000000000",
    "ValidationKey": "your-validation-key",
    "ProcessDate": "2024-01-15T10:30:00",
    "MusteriTipi": 1,
    "PaidAmount": 1500.00,
    "LeasePostingGroupId": true,
    "FirmaAdi": "Örnek Firma A.Ş.",
    "CurrencyCode": "TRY"
  }'
```
