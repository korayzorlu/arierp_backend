# krs — Kredi Risk Sınıflandırması

`LeasFlexToOracle.exe` (Program.cs) + `TRLEAS_UTIL_API.pck` (Oracle PL/SQL)
zincirinin, KRS raporu için gerekli kısmının Django/Python portu.

## Kurulum (arierp_backend'e gömme)

1. Bu `krs/` klasörünü projenizin kök dizinine (diğer app'lerinizle
   yan yana) kopyalayın.
2. `settings.py` -> `INSTALLED_APPS`'e `"krs"` ekleyin.
3. `krs/models.py`'nin en üstündeki `from common.models import Company`
   satırını, `Company` modelinizin gerçek import yoluna göre düzeltin.
4. `python manage.py makemigrations krs && python manage.py migrate krs`
5. Test edin: `python manage.py run_krs_pipeline 2`
6. Çalıştığını gördükten sonra `CELERY_BEAT_SCHEDULE`'a şunu ekleyin
   (saati kendinize göre ayarlayın — Otomatik_Kapama orijinalde diğer
   Leasflex çekme job'larından SONRA çalışıyordu, o yüzden mevcut
   `fetch-*-leaseflex-task` saatlerinizden sonraki bir saat seçmenizi
   öneririm):

   ```python
   "run-krs-pipeline-task": {
       "task": "krs.tasks.run_krs_pipeline_task",
       "schedule": crontab(minute=30, hour="5"),
       "args": [2],
   },
   ```

## Ne yapıyor, ne yapmıyor

**Kapsam dahili (port edildi, satır referansları orijinal dosyalara göre):**

- Program.cs `TEMERRUT_OLUSTUR` bloğundaki MSSQL sorgusu → `sql/kapama_hareketleri.sql`
- Program.cs'teki fatura/ödeme işaret normalizasyonu → `services/kapama.py::normalize_fatura_odeme`
- `TRLEAS_UTIL_API.Otomatik_Kapama` satır 483-517 (FIFO eşleştirme) → `services/kapama.py::fifo_kapama`
- Otomatik_Kapama satır 519-543 (temerrüt tutarı + bugüne kadar temerrüt hesabı) → aynı fonksiyon
- `TRLEAS_UTIL_API.Temerrut_Havuzu`'nun "tarihe göre snapshot" mantığı → `KrsTemerrutHavuz` modeli + `services/pipeline.py`

**Kapsam HARİCİ (bilinçli olarak alınmadı):**

- **`Protokol_Plan`** — yeniden yapılandırma/taksit planı üretimi. Bu,
  ileriye dönük ödeme planını değiştiriyor, KRS sınıflandırmasının
  girdisi değil. İhtiyaç duyarsanız ayrı bir modül olarak eklenebilir.
- **`Kira_Plani_Olustur`'daki türetilmiş sözleşme alanları** (leasing
  geliri, KDV toplamı, peşinat, vb.) ve içine gömülü, belirli
  sözleşmelere/TC kimlik numaralarına özel hardcoded yamalar. Bunlar
  genel iş kuralı değil, üretimde ortaya çıkmış tek seferlik
  düzeltmeler — bilerek kopyalanmadı. Gerekirse ayrı bir "veri
  düzeltme" mekanizmasıyla ele alınmalı, algoritmanın bir parçası gibi
  davranılmamalı.
- **`Get_Bakiye`** — genel amaçlı bakiye fonksiyonu, KRS akışını
  beslemiyor.
- **Lease/Contract modellerinize bağlama** — `KrsTemerrutHavuz`
  şu an sadece IFS'in kendi `contract_header_id`'sini saklıyor,
  `Lease` modelinize otomatik FK bağlamıyor (`models.py` içinde TODO
  olarak işaretli). `Lease` modelinizdeki hangi alanın
  `ContractHeaderId`'ye karşılık geldiğini netleştirdiğinizde kolayca
  eklenebilir.

## Bilerek korunan hatalar (BİREBİR UYUMLULUK kararınız üzerine)

Orijinal `Otomatik_Kapama` prosedüründe, gün-aralığı tiering mantığında
kopyala-yapıştır hataları var. Talebiniz üzerine bunlar **düzeltilmeden**
portlandı:

| Fonksiyon | Orijinaldeki hata | Pratik etki |
|---|---|---|
| `gecikmis_odeme_temerrut_orani` (temerrut_tutar) | 61-90 gün dilimi, 41-60 ile aynı koşulu tekrarlıyor, asla tetiklenmiyor | 61-90 gün arası gecikmeler için oran = 0 |
| `bugune_kadar_temerrut_orani` (bugune_kadar_temerrut) | Üç ELSIF de aynı koşulu (31-40) tekrarlıyor | 41-90 gün arası açık faturalar için oran = 0, sadece 31-40 ve 91+ çalışıyor |

Bu davranışı değiştirmek isterseniz **sadece** `services/kapama.py`
içindeki bu iki fonksiyonu güncellemeniz yeterli; `tests.py`'deki ilgili
testleri de güncellemeyi unutmayın (şu an bu hataların var olduğunu
doğrulayan testler yazıldı, "düzeltirseniz" o testler kırılacak — bu
kasıtlı, bir uyarı niteliğinde).

Ayrıca `temerrut_tutar` hesabı orijinalde faturanın **kendi** `odeme_tutar`
alanını baz alıyor (genelde 0, sadece o tarihte aynı satıra hem fatura hem
ödeme düşmüşse sıfırdan farklı oluyor) — "ödenen tutarı" baz almak daha
mantıklı görünse de, bu tuhaflık da birebir korunmuştur. Detay
`services/kapama.py` docstring'lerinde.

## EKSİK OLAN KRİTİK PARÇA: gerçek KRS/KRM sınıflandırma kuralı

`TRLEAS_KRS_API` / `TRLEAS_KRM_API` paketlerinin kaynak kodu elimizde
yoktu, dolayısıyla nihai "hangi gün aralığı hangi risk grubuna girer"
kuralı **doğrulanmamış bir varsayımdır** (`services/kapama.py::classify_risk_group`,
`models.py::RiskGrubu`). Gerçek kural elinize geçtiğinde:

1. `models.py`'deki `RiskGrubu` choices'ını güncelleyin (grup sayısı/adları farklı olabilir).
2. `services/kapama.py::classify_risk_group()` fonksiyonunu güncelleyin.

Pipeline'ın geri kalanına (FIFO, tiering, veri çekme) dokunmanız gerekmez —
bu fonksiyon tamamen izole.

## Test

```bash
python manage.py test krs
```

`tests.py`, saf Python mantığını (FIFO, tiering, normalize) DB'siz test
eder. MSSQL/Postgres bağlantısı gerektiren entegrasyon testi
eklenmemiştir — `python manage.py run_krs_pipeline <company_id>` ile elle
doğrulamanızı öneririz, ideal olarak ilk çalıştırmada IFS/Oracle'ın
ürettiği `TRLEAS_KAPAMA_TAB` / `trleas_temerrut_havuz_tab` ile birkaç
sözleşme üzerinden satır satır karşılaştırarak.
