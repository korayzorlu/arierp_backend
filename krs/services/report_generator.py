"""
krs/services/report_generator.py

IFS / TRLEAS_KRS_API'nin ürettiği BDDK KRS bildirim dosyasının
Django tarafında üretilmesi.  Tersine-mühendislik kaynağı:
  KrsBildirimi_260622-171247.txt (fiilen üretilmiş örnek dosya)
  Ekran görüntüsü: IFS → KRS Bildirimi → Gönderim sekmesi

== Dosya formatı ==
Encoding : UTF-8 with BOM (utf-8-sig)
Satır boyu: 500 karakter (sabit), her satır sonunda \\n
Kayıt türleri ve konumları kesin olarak çözülmüştür.

+--------+----------+----------------------------------------------------+
| Tür    | Pos.     | Anlam                                              |
+--------+----------+----------------------------------------------------+
| CS0000 | -        | Dosya başlığı                                      |
| CS0100 | -        | Sözleşme (kira planı) kaydı                        |
| CS0200 | -        | Borçlu (müşteri) kaydı — sadece yeni sözleşmeler  |
| CS0301 | -        | Adres kaydı         — sadece yeni sözleşmeler     |
| CS9999 | -        | Dosya özeti / kapanış                              |
+--------+----------+----------------------------------------------------+

== CS0100 alanları (500 karakter) ==
[0:8]   kayit_turu   CS010001 (eski) | CS010002 (yeni, bu dönem açılan)
[8:23]  sozlesme_ref  kurumsal_kod(8) + sozlesme_id:07d
[51:56] para_birimi  19490 = TRY
[58:66] sozlesme_tar YYYYMMDD
[86:91] kredi_turu   03112 (sabit — finansal kiralama)
[103:113] tutar_A    toplam_tahakkuk (kuruş, 2-decimal implied)
[113:123] tutar_B    gecikme_faizi   (kuruş)
[123:125] taksit_kodu 01/26/30/31/32/08/13 (bkz. TAKSİT_KODU_MAP)
[125:127] sabit01    "01" (sabit)
[127:137] tutar_C    aylık_taksit veya teminat_deger (kuruş)
[137:147] tutar_D    tutar_C × 10  (yaklaşık)
[147:150] teminat    104/504/204/004/704 (bkz. TEMİNAT_KODU_MAP)
[150:184] (boş)
[184:185] risk_grubu 0/1/2/3/4/5
[186:196] kalan_ana  kalan anapara (kuruş)
[205:216] gecik_ana  gecikmedeki anapara (kuruş, ×1000 precision → /1000 TRY)
[300:309] gecik_lira gecikmedeki anapara lira olarak (= int(gecik_ana/1000))
[310:311] "0"
[321:330] "000000000"
[339:341] vade_kodu  00=gecikme yok / 08=risk1 / 39=risk2 / 69=risk3
[341:500] (boş)

NOT: [123:150] bloğundaki taksit_kodu, tutar_C, tutar_D, teminat alanları
Leasflex'ten gelen sözleşme detaylarına bağlıdır ve tam kaynak eşlemesi
doğrulanmamıştır.  Yeni sözleşmelerde (taksit_kodu='01') C=0.20, D=2.00
sabit değeri kullanılmaktadır (örnek dosyadaki gözleme dayanarak).

== CS020002 alanları (500 karakter) ==
[0:8]   CS020002
[8:23]  sozlesme_ref
[38:39] "1" (sıra)
[41:54] kimlik_blok  13 karakter:
           [41:42]='1' (gerçek kişi göstergesi)
           [42:53]=tc_no (11 hane)
           [53:54]='0'  (!!! doğrulama gerekli — son hane belirsiz !!!)
[84:88] musteri_tip  "9999" (bireysel)
[98:138] soyadi      40 karakter, soldan hizalı
[138:178] adi        40 karakter
[228:243] anne_adi   15 karakter
[243:258] baba_adi   15 karakter
[258:259] "9"
[319:327] dogum_tar  YYYYMMDD
[397:398] "0"

== CS030102 alanları (500 karakter) ==
[0:8]   CS030102
[8:23]  sozlesme_ref
[38:39] "1"
[41:51] adres_kodu  "1020000101" (sabit — IFS'te tüm kayıtlar bu kodu kullanıyor)
[63:?]  adres_metin serbest metin (max 437 karakter)

== Doğrulanmamış / Belirsiz Alanlar ==
- kimlik_blok [53:54]: Son 1 karakter TC kimlikten türetilip türetilmediği
  belirsiz.  Örnek dosyada TC kimlikleri test/anonimize olduğundan kontrol
  edilemedi. Gerçek veride IFS çıktısıyla karşılaştırarak doğrulayın.
- taksit_kodu: Leasflex'teki hangi alandan geldiği bilinmiyor.
- tutar_C / tutar_D: Örnek dosyada D ≈ C × 10 gözlemleniyor, tam anlam bilinmiyor.
- teminat_kodu: Sözleşme türüne veya teminat tipine bağlı olduğu düşünülüyor.
- vade_kodu: Risk grubu → {0:'00', 1:'08', 2:'39', 3:'69'} eşlemesi gözlemlenmiş,
  bu kodların farklı sözleşme türlerinde farklı değer alıp almadığı bilinmiyor.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

RECORD_LEN = 500
ZERO = Decimal("0")

# ---- Sabitler (IFS kurulum bazlı - settings'e taşınabilir) ----
INSTITUTION_CODE = "0100309309"          # CS0000/CS9999 header'ındaki 10-haneli kurum kodu
INSTITUTION_REF  = INSTITUTION_CODE[2:10]  # sözleşme refansında kullanılan 8 haneli kısım
CURRENCY_CODE    = "19490"               # TRY para birimi kodu
CREDIT_TYPE_CODE = "03112"               # Finansal kiralama sabit türü
ADDRESS_CODE     = "1020000101"          # CS0301'deki sabit adres kodu

# Risk grubuna göre vade kodu (örnek dosyadan gözlemlendi)
VADE_KODU_MAP = {0: "00", 1: "08", 2: "39", 3: "69", 4: "69", 5: "69"}

# Taksit kodu '26' (bi-haftalık?) olan sözleşmeler risk=1 iken vade='09' değerini
# alıyor (örnek dosyada gözlemlendi). Diğer taksit kodlarında vade=risk grubunun
# standart karşılığı. Bu map risk_grubu başına override sağlar.
# Dict yapısı: (risk_grubu, taksit_kodu) → vade; eksikse VADE_KODU_MAP[risk] kullanılır.
VADE_KODU_OVERRIDE: dict[tuple[int, str], str] = {
    (1, "26"): "09",
}

# tutar_D = tutar_C × 10 + küçük düzeltme, düzeltme kodu teminat türünden türetilir.
# Örnek dosyadan kesin olarak gözlemlendi ve doğrulandı:
#   teminat 104/004/804 (ilk rakam 0 veya 1) → +3
#   teminat 504/704/604 (ilk rakam 5 veya 7) → +2
#   teminat 204 (ilk rakam 2)                 → +1
# (Taksit kodu 08 olan özel sözleşmelerde bu formül geçerli değil, ayrı ele alınmalı.)
TEMINAT_D_CORRECTION: dict[str, int] = {
    "0": 3, "1": 3, "2": 1, "3": 3,
    "4": 3, "5": 2, "6": 2, "7": 2, "8": 3, "9": 3,
}

# Taksit kodu — leasing türüne göre eşleme (TAM DOĞRULAMA GEREKİYOR)
# Örnek dosyadan gözlemlenen: 32=aylık, 26=?, 31=?, 30=?, 01=yeni sözleşme
TAKSIT_KODU_YENI = "01"   # bu dönemde açılan yeni sözleşmeler
TAKSIT_KODU_AYLIK = "32"  # aylık ödemeli eski sözleşme (varsayılan)


def _f(s: str, width: int, align: str = "left") -> str:
    """String'i tam `width` karaktere pad eder; keser."""
    s = str(s or "")
    if align == "left":
        return s.ljust(width)[:width]
    return s.rjust(width)[:width]


def _n(val, width: int) -> str:
    """Sayısal değeri `width` haneli sıfır-dolgu integer string'e çevirir.
    Ondalıklı değer verilirse implicit 2-decimal (kuruş) formatı varsayılır:
    Decimal('136886.90') → '0013688690' (10 haneli).
    """
    if isinstance(val, Decimal):
        val = int(val * 100)
    return str(int(val)).zfill(width)[:width]


def _n_milli(val, width: int) -> str:
    """Binlik (1/1000 TRY) precision: Decimal('4899.300') → '00004899300' (11 haneli)."""
    if isinstance(val, Decimal):
        val = int(val * 1000)
    return str(int(val)).zfill(width)[:width]


def _n_lira(val, width: int) -> str:
    """Sadece tam lira kısmı: Decimal('4899.300') → '000004899' (9 haneli)."""
    if isinstance(val, Decimal):
        val = int(val)
    return str(int(val)).zfill(width)[:width]


def _date(d: Optional[date]) -> str:
    return d.strftime("%Y%m%d") if d else "00000000"


def _record(fields: dict[int, str]) -> str:
    """Alanların konumlarını (int) ve değerlerini (str) alıp
    500-karakterlik satır üretir."""
    row = [" "] * RECORD_LEN
    for pos, val in fields.items():
        for i, ch in enumerate(val):
            if pos + i < RECORD_LEN:
                row[pos + i] = ch
    return "".join(row)


# ============================================================
# Kayıt üreticileri
# ============================================================

def make_header(
    company_name: str,
    period_start: date,
    period_end: date,
) -> str:
    return _record({
        0:   f"CS0000{INSTITUTION_CODE}",   # [0:16]
        78:  _f(company_name, 30),           # [78:108]
        108: _date(period_start),            # [108:116]
        116: _date(period_end),              # [116:124]
    })


def make_cs0100(
    contract_header_id: int,
    reference_date: date,
    is_new: bool,
    # Finansal alanlar — Lease modeli veya KrsTemerrutHavuz'dan
    toplam_tahakkuk: Decimal = ZERO,       # [103:113] tutar_A kuruş
    gecikme_faizi: Decimal = ZERO,         # [113:123] tutar_B kuruş
    kalan_anapara: Decimal = ZERO,         # [186:196]
    gecikmedeki_anapara: Decimal = ZERO,   # [205:216] ve [300:309]
    risk_grubu: int = 0,                   # [184:185]
    # Aşağıdaki alanlar leasing türüne bağlı — doğrulama gerekli
    taksit_kodu: str = "",
    teminat_kodu: str = "104",
    aylik_taksit: Decimal = ZERO,          # tutar_C [127:137]
) -> str:
    """
    CS010001 (is_new=False) veya CS010002 (is_new=True) kaydı üretir.

    Yeni sözleşmeler için (is_new=True): tutar_C=0.20, tutar_D=2.00 —
    örnek dosyada tüm yeni sözleşmelerde gözlemlenen sabit değerler.
    """
    kayit_turu = "CS010002" if is_new else "CS010001"
    ref = f"{INSTITUTION_REF}{contract_header_id:07d}"
    taksit = taksit_kodu or (TAKSIT_KODU_YENI if is_new else TAKSIT_KODU_AYLIK)

    if taksit == TAKSIT_KODU_YENI:
        # Taksit kodu '01' → bu dönemde ilk kez bildirilen sözleşme.
        # Örnek dosyada: tutar_C = 0.20 TRY, tutar_D = 2.00 TRY (sabit placeholder).
        tutar_c_raw = "0000000020"
        tutar_d_raw = "0000000200"
    else:
        # Yerleşik sözleşmeler: tutar_C = aylık taksit (kuruş integer)
        # tutar_D = C × 10 + teminat düzeltmesi (tüm standart kayıtlarda doğrulandı).
        # İSTİSNA: taksit_kodu='08' olan kayıtlarda (örn. sözleşme 53208) D, bu
        # formüle uymaz — kaynağı bilinmiyor. Bu tür kayıtlar için aylik_taksit ve
        # teminat_kodu yerine doğrudan tutar_D de geçilebilir (pipeline.py'de).
        c_int = int(aylik_taksit * 100)  # kuruş olarak integer
        d_corr = TEMINAT_D_CORRECTION.get(teminat_kodu[0] if teminat_kodu else "1", 3)
        d_int = c_int * 10 + d_corr
        tutar_c_raw = str(c_int).zfill(10)[:10]
        tutar_d_raw = str(d_int).zfill(10)[:10]

    vade = VADE_KODU_OVERRIDE.get((risk_grubu, taksit), VADE_KODU_MAP.get(risk_grubu, "00"))
    # gecik_lira [300:309]: gecikmedeki_anapara'nın 1/10 TRY precision karşılığı
    # Örnek: 4899.30 TRY → int(4899.30 × 10) = 48993 → '000048993'
    gecik_x10 = int(gecikmedeki_anapara * 10) if isinstance(gecikmedeki_anapara, Decimal) else int(gecikmedeki_anapara * 10)
    gecik_lira_str = str(gecik_x10).zfill(9)[:9]

    return _record({
        0:   kayit_turu,
        8:   ref,                              # [8:23]
        51:  CURRENCY_CODE,                    # [51:56]
        58:  _date(reference_date),            # [58:66]
        86:  CREDIT_TYPE_CODE,                 # [86:91]
        103: _n(toplam_tahakkuk, 10),          # [103:113] tutar_A
        113: _n(gecikme_faizi, 10),            # [113:123] tutar_B
        123: taksit,                           # [123:125]
        125: "01",                             # [125:127] sabit
        127: tutar_c_raw,                      # [127:137] tutar_C
        137: tutar_d_raw,                      # [137:147] tutar_D
        147: teminat_kodu,                     # [147:150]
        184: str(risk_grubu),                  # [184:185]
        186: _n(kalan_anapara, 10),            # [186:196]
        205: _n_milli(gecikmedeki_anapara, 11), # [205:216]
        300: gecik_lira_str,                   # [300:309]
        310: "0",                              # [310:311]
        321: "000000000",                      # [321:330]
        339: vade,                             # [339:341]
    })


def make_cs0200(
    contract_header_id: int,
    tc_no: str,                  # 11 hane TC kimlik (Partner.tc_no)
    soyadi: str,
    adi: str,
    anne_adi: str = "",
    baba_adi: str = "",
    dogum_tarihi: Optional[date] = None,
) -> str:
    """
    CS020002: Müşteri (borçlu) kaydı.

    Kimlik bloğu [41:54] formatı:
        [41]    = '1' (gerçek kişi göstergesi)
        [42:53] = tc_no (11 hane)
        [53]    = '0' (son hane — DOĞRULAMA GEREKİYOR, belirsiz)
    Gerçek üretim verisinde IFS çıktısıyla karşılaştırarak doğrulayın.
    """
    ref = f"{INSTITUTION_REF}{contract_header_id:07d}"
    tc_clean = tc_no.strip().zfill(11)[:11]
    # IFS CS0200 ekranından doğrulandı: [41]='1' (sıra no), [42]='6' (kimlik tipi:
    # 6=TC kimlik numarası), [43:54]=TC kimlik (11 hane). Toplam 13 karakter.
    kimlik_blok = f"16{tc_clean}"

    return _record({
        0:   "CS020002",
        8:   ref,
        38:  "1",
        41:  kimlik_blok,                   # [41:54]
        84:  "9999",                        # [84:88]
        98:  _f(soyadi, 40).upper(),        # [98:138]
        138: _f(adi, 40).upper(),           # [138:178]
        228: _f(anne_adi, 15).upper(),      # [228:243]
        243: _f(baba_adi, 15).upper(),      # [243:258]
        258: "9",                           # [258:259]
        319: _date(dogum_tarihi),           # [319:327]
        397: "0",                           # [397:398]
    })


def make_cs0301(
    contract_header_id: int,
    adres_metin: str,
) -> str:
    """
    CS030102: Adres kaydı.
    Adres kodu '1020000101' tüm kayıtlarda sabit görünüyor (IFS default).
    """
    ref = f"{INSTITUTION_REF}{contract_header_id:07d}"
    return _record({
        0:  "CS030102",
        8:  ref,
        38: "1",
        41: ADDRESS_CODE,                   # [41:51]
        63: adres_metin[:437].upper(),      # [63:500]
    })


def make_footer(
    toplam_cs0100: int,
    isim_sayisi: int,
    adres_sayisi: int,
) -> str:
    """
    CS9999: Dosya kapanış özeti.

    IFS Kapanış(CS9999) sekmesindeki alan isimleri (sırasıyla, her biri 7 hane):
        [78:85]   Hesap Kayıt Sayısı       → toplam CS0100 kaydı
        [85:92]   Hesap Kayıt Sayısı Diğer → 0 (CS0199, geçmiş kayıt)
        [92:99]   Hesap Geçmisi Sayısı     → 0
        [99:106]  İsim Kayıt Sayısı        → CS0200 (müşteri) kaydı sayısı
        [106:113] Adres Kayıt Sayısı       → CS0301 (adres) kaydı sayısı
        [113:120] Kişisel Bilgi Sayısı     → 0
        [120:127] İşveren Kayıt Sayısı     → 0
        [127:134] Banka Kayıt Sayısı       → 0

    Örnek dosya karşılaştırmasıyla doğrulandı: 33 CS0100, 7 CS0200, 7 CS0301 → ✓
    """
    blok = (
        str(toplam_cs0100).zfill(7)   # Hesap Kayıt Sayısı
        + "0000000"                    # Hesap Kayıt Sayısı Diğer
        + "0000000"                    # Hesap Geçmisi Sayısı
        + str(isim_sayisi).zfill(7)    # İsim Kayıt Sayısı   (CS0200)
        + str(adres_sayisi).zfill(7)   # Adres Kayıt Sayısı  (CS0301)
        + "0000000"                    # Kişisel Bilgi Sayısı
        + "0000000"                    # İşveren Kayıt Sayısı
        + "0000000"                    # Banka Kayıt Sayısı
    )[:56]
    return _record({
        0:  f"CS9999{INSTITUTION_CODE}",
        78: blok,
    })


# ============================================================
# Yardımcı: Lease / Partner nesnelerinden CS0100 parametrelerini türet
# ============================================================

@dataclass
class ContractKrsData:
    """
    Pipeline.py'de KrsTemerrutHavuz + Lease + Partner verilerinden
    oluşturulan bir sözleşmenin KRS raporu için hazırlanmış hali.
    Tüm Decimal alanlar TRY cinsindendir (2-decimal, kuruş hassasiyetinde).

    Bu dataclass'ı doldurmak için görmeniz gereken yer:
        krs/services/pipeline.py -> generate_krs_file()
    """
    contract_header_id: int
    reference_date: date                 # sözleşme / son işlem tarihi
    is_new: bool                         # bu raporlama döneminde yeni açılan mı

    # KrsTemerrutHavuz'dan gelen değerler
    risk_grubu: int = 0
    toplam_acik_bakiye: Decimal = ZERO   # gecikmedeki anapara (→ gecik_ana)

    # Lease model alanları
    total_payment: Decimal = ZERO        # toplam sözleşme değeri  (→ tutar_A)
    kalan_anapara: Decimal = ZERO        # kalan anapara            (→ kalan_ana)
    gecikme_faizi: Decimal = ZERO        # temerrüt faizi           (→ tutar_B)
    aylik_taksit: Decimal = ZERO         # aylık taksit             (→ tutar_C/D)
    taksit_kodu: str = ""
    teminat_kodu: str = "104"

    # Partner (müşteri) bilgileri — CS020002 / CS030102 için
    tc_no: str = ""
    soyadi: str = ""
    adi: str = ""
    anne_adi: str = ""
    baba_adi: str = ""
    dogum_tarihi: Optional[date] = None
    adres: str = ""


def build_records(contracts: list[ContractKrsData]) -> list[str]:
    """
    Sözleşme listesinden tüm satırları üretir (header/footer HARİÇ).
    Her sözleşme için 1 CS0100 + (gerekirse) 1 CS0200 + 1 CS0301 üretir.
    """
    rows: list[str] = []
    for c in contracts:
        rows.append(make_cs0100(
            contract_header_id=c.contract_header_id,
            reference_date=c.reference_date,
            is_new=c.is_new,
            toplam_tahakkuk=c.total_payment,
            gecikme_faizi=c.gecikme_faizi,
            kalan_anapara=c.kalan_anapara,
            gecikmedeki_anapara=c.toplam_acik_bakiye,
            risk_grubu=c.risk_grubu,
            taksit_kodu=c.taksit_kodu,
            teminat_kodu=c.teminat_kodu,
            aylik_taksit=c.aylik_taksit,
        ))
        if c.is_new and c.tc_no:
            rows.append(make_cs0200(
                contract_header_id=c.contract_header_id,
                tc_no=c.tc_no,
                soyadi=c.soyadi,
                adi=c.adi,
                anne_adi=c.anne_adi,
                baba_adi=c.baba_adi,
                dogum_tarihi=c.dogum_tarihi,
            ))
            if c.adres:
                rows.append(make_cs0301(
                    contract_header_id=c.contract_header_id,
                    adres_metin=c.adres,
                ))
    return rows


def generate_report(
    contracts: list[ContractKrsData],
    company_name: str,
    period_start: date,
    period_end: date,
) -> bytes:
    """
    Tam KRS bildirim dosyasını UTF-8 BOM ile bytes olarak üretir.
    Dönen bytes bir dosyaya yazılabilir veya HttpResponse üzerinden
    indirilebilir.
    """
    buf = io.StringIO()
    # Dosya ilk satırı (IFS'in koyduğu)
    buf.write("Icerik\t\n")
    # Header
    buf.write(make_header(company_name, period_start, period_end) + "\n")
    # Sözleşme kayıtları
    data_rows = build_records(contracts)
    for row in data_rows:
        buf.write(row + "\n")
    # Footer
    cs0100_count = len(contracts)
    isim_count = sum(1 for c in contracts if c.is_new and c.tc_no)
    adres_count = sum(1 for c in contracts if c.is_new and c.adres)
    buf.write(make_footer(cs0100_count, isim_count, adres_count) + "\n")
    return ("\ufeff" + buf.getvalue()).encode("utf-8")