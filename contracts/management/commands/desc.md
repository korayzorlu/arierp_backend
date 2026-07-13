### Request Body Parametreleri

| Alan                         | Tip                                   | Zorunlu | Açıklama                                                                      |
| ---------------------------- | ------------------------------------- | ------- | ------------------------------------------------------------------------------- |
| `CompanyId`                | string                                | Evet    | Şirket ID'si                                                                   |
| `ValidationKey`            | string                                | Evet    | Doğrulama kodu                                                                 |
| `ContractHeaderCode`       | string                                | Evet    | Para birimi kodu, varsayılan TRY                                               |
| `CustomerName`             | string                                | Evet    | Müşteri adı-soyadı                                                          |
| `TaxAndTCIdentity`         | string                                | Evet    | Müşteri TC/VKN/Pasaport No                                                    |
| `YazismaAddress`           | string                                | Evet    | Yazışma adresi, resmi adres                                                   |
| `WorkPhone`                | string                                | Hayır  | İş telefonu                                                                   |
| `OtherAddress`             | string                                | Hayır  | Yurt dışı adresi                                                             |
| `MobilPhone`               | string                                | Hayır  | Cep tel                                                                         |
| `OtherPhone`               | string                                | Hayır  | Yurt dışı tel                                                                |
| `Email`                    | string                                | Hayır  | E-posta adresi                                                                  |
| `Kep`                      | string                                | Hayır  | Kep adresi                                                                      |
| `IslandNo`                 | string                                | Evet    | Ada no                                                                          |
| `ParcelNo`                 | string                                | Evet    | Parsel no                                                                       |
| `ProjectName`              | string                                | Evet    | Proje ismi                                                                      |
| `FreePartUnitType`         | string                                | Evet    | Ünite/daire tipi                                                               |
| `ApartmentTypeName`        | string                                | Hayır  | Bina tipi                                                                       |
| `FreeValidationPeriodText` | string                                | Hayır  | Paket modeli                                                                    |
| `TimeSharePeriodPartText`  | string                                | Evet    | Devre tatil dönemi                                                             |
| `NumberOfPeopleStay`       | integer                               | Evet    | Maksimum konaklayacak kişi sayısı                                            |
| `CustomerSignDate`         | string (date, format: "YYYY-MM-DD") | Evet    | Sözleşme/imza tarihi                                                          |
| `TaxRate`                  | integer                               | Evet    | KDV oranı                                                                      |
| `PlannedDeliveryDate`      | string (date, format: "YYYY-MM-DD") | Hayır  | Planlanan teslim tarihi                                                         |
| `Maturity`                 | integer                               | Hayır  | Ödeme süresi                                                                  |
| `CashSalesTotalAmount`     | string (decimal, format: "0.00")     | Hayır  | Devre tatil baz maliyeti. Nokta ondalık ayracı ile, 2 hane (örn. "1234.50") |
| `LeasingAmount`            | string (decimal, format: "0.00")     | Hayır  | Finansal kiralama geliri. Nokta ondalık ayracı ile, 2 hane (örn. "1234.50")  |
| `CurrentSaleTotalAmount`   | string (decimal, format: "0.00")     | Evet    | Toplam sözleşme bedeli. Nokta ondalık ayracı ile, 2 hane (örn. "1234.50")  |
| `DownPaymentAmount`        | string (decimal, format: "0.00")     | Hayır  | Peşinat tutarı. Nokta ondalık ayracı ile, 2 hane (örn. "1234.50")          |
| `CurrencyCode`             | string (enum: TRY, USD, EUR)          | Evet    | Para birimi                                                                     |
