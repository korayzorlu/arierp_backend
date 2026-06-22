"""
krs/tests.py

Bu testler bilerek `unittest.TestCase` kullanır (Django TestCase değil) -
test edilen fonksiyonlar saf Python (dataclass tabanlı), veritabanı
gerektirmiyor. `python manage.py test krs` ile çalışır.
"""

from datetime import date
from decimal import Decimal
from unittest import TestCase

from krs.services.kapama import (
    KapamaSatiri,
    bugune_kadar_temerrut_orani,
    fifo_kapama,
    gecikmis_odeme_temerrut_orani,
    hesapla_acik_durum,
    normalize_fatura_odeme,
)


class NormalizeFaturaOdemeTests(TestCase):
    def test_pozitif_odeme_faturaya_eklenir(self):
        fatura, odeme = normalize_fatura_odeme(Decimal("100"), Decimal("50"))
        self.assertEqual(fatura, Decimal("150"))
        self.assertEqual(odeme, Decimal("0"))

    def test_negatif_fatura_odemeye_eklenir(self):
        fatura, odeme = normalize_fatura_odeme(Decimal("-30"), Decimal("-100"))
        self.assertEqual(fatura, Decimal("0"))
        self.assertEqual(odeme, Decimal("-130"))

    def test_normal_durum_degismez(self):
        fatura, odeme = normalize_fatura_odeme(Decimal("100"), Decimal("-50"))
        self.assertEqual(fatura, Decimal("100"))
        self.assertEqual(odeme, Decimal("-50"))


class TieringBugPreservationTests(TestCase):
    """Bu testler, kullanıcı talebiyle KASITLI olarak korunan PL/SQL
    hatalarının Python tarafında da aynı şekilde çalıştığını doğrular.
    Eğer ileride bu hatalar düzeltilirse, bu testler de güncellenmelidir."""

    def test_gecikmis_odeme_61_90_gun_olu_kod(self):
        # 61-90 gün dilimi orijinalde hiç tetiklenmiyor -> oran 0 olmalı
        self.assertEqual(gecikmis_odeme_temerrut_orani(75), Decimal("0.00"))

    def test_gecikmis_odeme_diger_dilimler(self):
        self.assertEqual(gecikmis_odeme_temerrut_orani(35), Decimal("0.02"))
        self.assertEqual(gecikmis_odeme_temerrut_orani(50), Decimal("0.05"))
        self.assertEqual(gecikmis_odeme_temerrut_orani(120), Decimal("0.10"))
        self.assertEqual(gecikmis_odeme_temerrut_orani(10), Decimal("0.00"))

    def test_bugune_kadar_41_90_gun_olu_kod(self):
        # 41-60 ve 61-90 dilimleri orijinalde hiç tetiklenmiyor -> oran 0
        self.assertEqual(bugune_kadar_temerrut_orani(50), Decimal("0.00"))
        self.assertEqual(bugune_kadar_temerrut_orani(75), Decimal("0.00"))

    def test_bugune_kadar_diger_dilimler(self):
        self.assertEqual(bugune_kadar_temerrut_orani(35), Decimal("0.02"))
        self.assertEqual(bugune_kadar_temerrut_orani(120), Decimal("0.10"))


class FifoKapamaTests(TestCase):
    def test_tek_fatura_tek_odeme_tam_kapanir(self):
        satirlar = [
            KapamaSatiri(1, date(2026, 1, 1), fatura_tutar=Decimal("1000")),
            KapamaSatiri(1, date(2026, 1, 15), odeme_tutar=Decimal("-1000")),
        ]
        detaylar = fifo_kapama(satirlar, rapor_tarihi=date(2026, 1, 20))

        self.assertEqual(len(detaylar), 1)
        self.assertEqual(detaylar[0].kapatilan_tutar, Decimal("1000"))
        fatura = satirlar[0]
        self.assertEqual(fatura.kapatilan_fatura_tutar, Decimal("1000"))
        self.assertEqual(fatura.acik_tutar, Decimal("0"))

    def test_kismi_odeme_en_eski_faturayi_once_kapar(self):
        satirlar = [
            KapamaSatiri(1, date(2026, 1, 1), fatura_tutar=Decimal("1000")),
            KapamaSatiri(1, date(2026, 2, 1), fatura_tutar=Decimal("1000")),
            KapamaSatiri(1, date(2026, 2, 15), odeme_tutar=Decimal("-600")),
        ]
        fifo_kapama(satirlar, rapor_tarihi=date(2026, 2, 20))

        ilk_fatura, ikinci_fatura, _ = satirlar
        self.assertEqual(ilk_fatura.kapatilan_fatura_tutar, Decimal("600"))
        self.assertEqual(ikinci_fatura.kapatilan_fatura_tutar, Decimal("0"))

    def test_fazla_odeme_sentetik_satir_olusturur(self):
        satirlar = [
            KapamaSatiri(1, date(2026, 1, 1), fatura_tutar=Decimal("1000")),
            KapamaSatiri(1, date(2026, 1, 15), odeme_tutar=Decimal("-1200")),
        ]
        detaylar = fifo_kapama(satirlar, rapor_tarihi=date(2026, 1, 20))

        # Sentetik satırın tarihi, sözleşmenin TÜM satırları arasındaki en
        # son tarih + 1 gündür (orijinal PL/SQL'deki "select max(tarih) from
        # trleas_kapama_tab where contract_header_id=..." mantığıyla aynı -
        # bu sorgu hem fatura hem ödeme satırlarını kapsar). Burada en son
        # tarih ödeme tarihi olan 15 Ocak'tır, dolayısıyla yeni tarih 16
        # Ocak olur (faturanın kendi tarihi olan 1 Ocak'tan değil).
        sentetik = [s for s in satirlar if s.sentetik]
        self.assertEqual(len(sentetik), 1)
        self.assertEqual(sentetik[0].fatura_tutar, Decimal("200"))
        self.assertEqual(sentetik[0].tarih, date(2026, 1, 16))
        self.assertEqual(len(detaylar), 2)

    def test_gec_odeme_temerrut_tutari_hesaplanir(self):
        # Fatura 1 Ocak'ta, ödeme 10 Şubat'ta (40 gün gecikme) -> %2
        satirlar = [
            KapamaSatiri(1, date(2026, 1, 1), fatura_tutar=Decimal("1000"), odeme_tutar=Decimal("0")),
            KapamaSatiri(1, date(2026, 2, 10), odeme_tutar=Decimal("-1000")),
        ]
        fifo_kapama(satirlar, rapor_tarihi=date(2026, 2, 15))
        # fatura satırının kendi odeme_tutarı 0 olduğu için temerrut_tutar da
        # 0 olmalı (orijinal PL/SQL davranışı - bkz. kapama.py docstring'i)
        self.assertEqual(satirlar[0].temerrut_tutar, Decimal("0.00"))

    def test_acik_durum_ozeti(self):
        satirlar = [
            KapamaSatiri(1, date(2026, 1, 1), fatura_tutar=Decimal("1000")),
            KapamaSatiri(1, date(2026, 2, 1), fatura_tutar=Decimal("500")),
        ]
        fifo_kapama(satirlar, rapor_tarihi=date(2026, 3, 1))
        durum = hesapla_acik_durum(satirlar, rapor_tarihi=date(2026, 3, 1))

        self.assertEqual(durum["en_eski_acik_fatura_tarihi"], date(2026, 1, 1))
        self.assertEqual(durum["toplam_acik_bakiye"], Decimal("1500"))
        self.assertEqual(durum["en_eski_acik_fatura_gecikme_gun"], 59)
