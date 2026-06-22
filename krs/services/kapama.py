"""
krs/services/kapama.py

TRLEAS_UTIL_API.Otomatik_Kapama (Oracle PL/SQL) prosedürünün, sadece
KRS sınıflandırması için gerekli kısmının Python portu.

KAPSAM DAHİLİ (port edildi):
    - Ödeme/fatura işaret normalizasyonu (Program.cs CariHareket mantığı)
    - FIFO fatura/ödeme eşleştirmesi (Otomatik_Kapama satır 483-517)
    - Gecikme tutarına göre temerrüt tutarı hesabı (satır 519-531)
    - Bugüne kadarki temerrüt hesabı (satır 532-543)

KAPSAM HARİCİ (bilinçli olarak alınmadı, README.md'de detaylı açıklama var):
    - Protokol_Plan (yeniden yapılandırma/taksit planı üretimi)
    - Kira_Plani_Olustur'daki türetilmiş sözleşme alanları (leasing geliri,
      KDV toplamı, vb.) ve içindeki sözleşmeye özel hardcoded yamalar
    - Get_Bakiye (genel bakiye fonksiyonu, KRS sınıflandırmasını beslemiyor)
    - Sözleşmenin gerçek IFS/Lease modeliyle eşleştirilmesi (TODO olarak
      models.py'de bırakıldı)

!!! BİREBİR UYUMLULUK KARARI (kullanıcı talebi) !!!
Orijinal PL/SQL'de mevcut olan gün-aralığı hataları KASITLI OLARAK
KORUNMUŞTUR, geçmiş raporlarla tutarlılık bozulmasın diye. Bu hatalar
gecikmis_odeme_temerrut_orani() ve bugune_kadar_temerrut_orani()
fonksiyonlarında açıkça işaretlenmiştir. Gerçek/düzeltilmiş davranış
istenirse SADECE bu iki fonksiyonu güncellemeniz yeterli.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

ZERO = Decimal("0.00")


@dataclass
class KapamaSatiri:
    """TRLEAS_KAPAMA_TAB'daki bir satırın (sözleşme + tarih) karşılığı."""

    contract_header_id: int
    tarih: date
    fatura_tutar: Decimal = ZERO
    odeme_tutar: Decimal = ZERO          # negatif değer = ödeme
    odenmis_temerrut: Decimal = ZERO     # MSSQL sorgusundaki "odenen_temerrut"
    gercek_odeme_tutar: Decimal = ZERO   # MSSQL sorgusundaki "odeme_kaydi"
    protokol: Decimal = ZERO

    # Bu üç alan FIFO eşleştirmesi sırasında hesaplanır, girdi olarak gelmez:
    kapatilan_fatura_tutar: Decimal = ZERO
    temerrut_tutar: Decimal = ZERO
    bugune_kadar_temerrut: Decimal = ZERO

    sentetik: bool = False  # fazla ödeme nedeniyle otomatik oluşturulan satır mı

    @property
    def acik_tutar(self) -> Decimal:
        return self.fatura_tutar - self.kapatilan_fatura_tutar


@dataclass
class KapamaDetay:
    """TRLEAS_KAPAMA_DETAY_TAB'daki bir satırın karşılığı: hangi ödeme,
    hangi faturayı, ne kadar kapattı."""

    contract_header_id: int
    odeme_tarihi: date
    fatura_tarihi: date
    kapatilan_tutar: Decimal


def normalize_fatura_odeme(fatura_tutar, odeme_tutar) -> tuple[Decimal, Decimal]:
    """
    Program.cs / TEMERRUT_OLUSTUR bloğundaki işaret düzeltmesinin birebir
    portu (satır ~2264-2273): aynı satırda fatura ve ödeme tutarı "ters
    işaretli" geldiğinde bunları tek kutuya topluyor.

        if OdemeTutar > 0:
            FaturaTutar += OdemeTutar; OdemeTutar = 0
        elif FaturaTutar < 0:
            OdemeTutar += FaturaTutar; FaturaTutar = 0
    """
    fatura_tutar = Decimal(fatura_tutar or 0)
    odeme_tutar = Decimal(odeme_tutar or 0)
    if odeme_tutar > 0:
        fatura_tutar += odeme_tutar
        odeme_tutar = ZERO
    elif fatura_tutar < 0:
        odeme_tutar += fatura_tutar
        fatura_tutar = ZERO
    return fatura_tutar, odeme_tutar


def gecikmis_odeme_temerrut_orani(gun: int) -> Decimal:
    """
    Otomatik_Kapama satır 522-530 (temerrut_tutar hesabı) birebir portu.

    Orijinal PL/SQL:
        IF    gun BETWEEN 31 AND 40 THEN orani := 0.02;
        ELSIF gun BETWEEN 41 AND 60 THEN orani := 0.05;
        ELSIF gun BETWEEN 41 AND 60 THEN orani := 0.08;  -- << HATA: 61-90 olması
                                                          --    gerekirken yine
                                                          --    41-60 yazılmış,
                                                          --    bu yüzden bu dal
                                                          --    HİÇBİR ZAMAN
                                                          --    çalışmaz.
        ELSIF gun >= 91          THEN orani := 0.10;

    Efektif (gerçekte çalışan) davranış: 31-40 gün -> %2, 41-60 gün -> %5,
    61-90 gün -> %0 (ölü kod), 91+ gün -> %10.

    !!! Bu hata kullanıcı talebiyle KASITLI OLARAK korunmuştur. Düzeltmek
    isterseniz üçüncü dalın koşulunu "41 <= gun <= 60" yerine
    "61 <= gun <= 90" yapmanız yeterli. !!!
    """
    if 31 <= gun <= 40:
        return Decimal("0.02")
    elif 41 <= gun <= 60:
        return Decimal("0.05")
    elif 41 <= gun <= 60:  # noqa: bilerek bırakılan orijinal hata - bkz. docstring
        return Decimal("0.08")
    elif gun >= 91:
        return Decimal("0.10")
    return ZERO


def bugune_kadar_temerrut_orani(gun: int) -> Decimal:
    """
    Otomatik_Kapama satır 532-543 (bugune_kadar_temerrut hesabı) birebir
    portu.

    Orijinal PL/SQL'de üç ayrı ELSIF de AYNI koşulu (gun BETWEEN 31 AND 40)
    tekrarlıyor (kopyala-yapıştır hatası). Efektif davranış: 31-40 gün -> %2
    (ilk dal her zaman kazanır), 41-90 gün -> %0 (üç dal da ölü kod), 91+
    gün -> %10.

    !!! Bu hata kullanıcı talebiyle KASITLI OLARAK korunmuştur. !!!
    """
    if 31 <= gun <= 40:
        return Decimal("0.02")
    elif 31 <= gun <= 40:  # noqa: orijinalde 41-60 olması gerekirken yine 31-40
        return Decimal("0.05")
    elif 31 <= gun <= 40:  # noqa: orijinalde 61-90 olması gerekirken yine 31-40
        return Decimal("0.08")
    elif gun >= 91:
        return Decimal("0.10")
    return ZERO


def fifo_kapama(satirlar: list[KapamaSatiri], rapor_tarihi: date) -> list[KapamaDetay]:
    """
    Otomatik_Kapama satır 483-543'ün birebir portu: FIFO fatura/ödeme
    eşleştirmesi + temerrüt hesapları.

    `satirlar`: TEK BİR sözleşmeye ait satırların listesi (tarihe göre
    sıralı olması gerekmez, fonksiyon kendi sıralar). Liste YERİNDE
    (in place) güncellenir: kapatilan_fatura_tutar, temerrut_tutar,
    bugune_kadar_temerrut alanları doldurulur; gerekirse fazla ödeme
    nedeniyle yeni "sentetik" satırlar listeye eklenir.

    Dönüş: TRLEAS_KAPAMA_DETAY_TAB karşılığı detay kayıtları.
    """
    if not satirlar:
        return []

    contract_id = satirlar[0].contract_header_id
    detaylar: list[KapamaDetay] = []

    odeme_satirlari = sorted(
        (s for s in satirlar if s.odeme_tutar < 0),
        key=lambda s: s.tarih,
    )

    for odeme in odeme_satirlari:
        kalan_odeme = abs(odeme.odeme_tutar)

        # Orijinal PL/SQL'deki cursor FOR loop gibi: açık fatura listesi bu
        # ödeme işlenmeye BAŞLARKEN bir kere alınır (tarihe göre artan).
        acik_faturalar = sorted(
            (s for s in satirlar if s.acik_tutar > 0),
            key=lambda s: s.tarih,
        )

        for fatura in acik_faturalar:
            if kalan_odeme <= 0:
                break
            acik_tutar = fatura.acik_tutar
            if kalan_odeme > acik_tutar:
                kalan_odeme -= acik_tutar
                detaylar.append(KapamaDetay(contract_id, odeme.tarih, fatura.tarih, acik_tutar))
                fatura.kapatilan_fatura_tutar = fatura.fatura_tutar
            else:
                fatura.kapatilan_fatura_tutar += kalan_odeme
                detaylar.append(KapamaDetay(contract_id, odeme.tarih, fatura.tarih, kalan_odeme))
                kalan_odeme = ZERO

        if kalan_odeme > 0:
            # Fazla ödeme: orijinal kod, en son tarihten bir gün sonrasına
            # "kredi/avans" niteliğinde sentetik bir fatura satırı açıyor.
            son_tarih = max((s.tarih for s in satirlar), default=odeme.tarih)
            yeni_tarih = son_tarih + timedelta(days=1)
            detaylar.append(KapamaDetay(contract_id, odeme.tarih, yeni_tarih, kalan_odeme))
            satirlar.append(
                KapamaSatiri(
                    contract_header_id=contract_id,
                    tarih=yeni_tarih,
                    fatura_tutar=kalan_odeme,
                    kapatilan_fatura_tutar=kalan_odeme,
                    sentetik=True,
                )
            )

    # ---- temerrut_tutar: ödeme anında geç kalınan gün sayısına göre ----
    # NOT: orijinal PL/SQL burada "rec_.odeme_tutar" yani FATURA satırının
    # KENDİ odeme_tutar alanını baz alıyor (genelde 0 olur, sadece o tarihte
    # aynı satıra hem fatura hem ödeme düşmüşse sıfırdan farklı olur). Bu,
    # orijinal kodun tuhaf ama gerçek davranışıdır; "doğru" olan muhtemelen
    # ödenen tutarı baz almaktı, ama talebiniz üzerine birebir korunmuştur.
    fatura_by_tarih = {s.tarih: s for s in satirlar}
    for d in detaylar:
        fatura = fatura_by_tarih.get(d.fatura_tarihi)
        if fatura is None:
            continue
        gun = (d.odeme_tarihi - d.fatura_tarihi).days
        oran = gecikmis_odeme_temerrut_orani(gun)
        if oran:
            fatura.temerrut_tutar += abs(fatura.odeme_tutar) * oran

    # ---- bugune_kadar_temerrut: rapor tarihi itibariyle hâlâ açık olanlar ----
    for s in satirlar:
        if s.acik_tutar <= 0:
            continue
        gun = (rapor_tarihi - s.tarih).days
        oran = bugune_kadar_temerrut_orani(gun)
        if oran:
            s.bugune_kadar_temerrut = s.acik_tutar * oran

    return detaylar


def hesapla_acik_durum(satirlar: list[KapamaSatiri], rapor_tarihi: date) -> dict:
    """
    fifo_kapama() çalıştırıldıktan SONRA çağrılır. Sözleşmenin rapor tarihi
    itibariyle açık (kapanmamış) durumunu özetler - KRS sınıflandırmasının
    girdisi budur.
    """
    acik = [s for s in satirlar if s.acik_tutar > 0]
    if not acik:
        return {
            "en_eski_acik_fatura_tarihi": None,
            "en_eski_acik_fatura_gecikme_gun": 0,
            "toplam_acik_bakiye": ZERO,
            "toplam_bugune_kadar_temerrut": sum((s.bugune_kadar_temerrut for s in satirlar), ZERO),
        }
    en_eski = min(acik, key=lambda s: s.tarih)
    return {
        "en_eski_acik_fatura_tarihi": en_eski.tarih,
        "en_eski_acik_fatura_gecikme_gun": max((rapor_tarihi - en_eski.tarih).days, 0),
        "toplam_acik_bakiye": sum((s.acik_tutar for s in acik), ZERO),
        "toplam_bugune_kadar_temerrut": sum((s.bugune_kadar_temerrut for s in satirlar), ZERO),
    }


def classify_risk_group(gecikme_gun: int) -> Optional[str]:
    """
    !!! YER TUTUCU - GERÇEK KRS/KRM SINIFLANDIRMA KURALI TANIMLI DEĞİL !!!

    TRLEAS_KRS_API / TRLEAS_KRM_API paketlerinin kaynak kodu elinizde
    olmadığı için, bu fonksiyon BDDK'nın finansal kiralama şirketleri için
    genel olarak kullandığı gün-aralığı mantığına BENZER, ama DOĞRULANMAMIŞ
    bir varsayım kullanır. Gerçek kural elinize geçtiğinde SADECE bu
    fonksiyonu (ve isterseniz models.RiskGrubu choices'ını) güncelleyin -
    pipeline'ın geri kalanına dokunmanız gerekmez.
    """
    from .. import models  # döngüsel import'tan kaçınmak için burada

    if gecikme_gun <= 0:
        return models.RiskGrubu.GRUP_1
    elif gecikme_gun <= 90:
        return models.RiskGrubu.GRUP_2
    elif gecikme_gun <= 180:
        return models.RiskGrubu.GRUP_3
    elif gecikme_gun <= 365:
        return models.RiskGrubu.GRUP_4
    else:
        return models.RiskGrubu.GRUP_5
