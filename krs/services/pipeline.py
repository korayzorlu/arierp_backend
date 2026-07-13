"""
krs/services/pipeline.py

Tüm KRS akışını baştan sona koşan orkestrasyon katmanı:
  1. Leasflex (MSSQL) -> kapama hareketlerini çek
  2. Sözleşme bazında grupla
  3. İşaret normalizasyonu + FIFO eşleştirme + temerrüt hesapları
  4. Açık durum özetini çıkar, risk grubunu belirle
  5. Sonuçları Postgres'e yaz (KapamaHareketi, KapamaDetay, KrsTemerrutHavuz)

== Çalışma modları ==

GÜNLÜK MOD (mod='daily') — IFS'in günlük raporuyla aynı mantık:
  Leasflex'ten TÜM geçmiş çekilir (FIFO doğruluğu için gerekli).
  Ancak KrsTemerrutHavuz'a yalnızca rapor_tarihi'nde vadesi gelen taksiti
  olan sözleşmeler yazılır (TrnDueDate == rapor_tarihi).
  Neden? IFS günlük KRS raporunu tam olarak bu şekilde üretiyor:
  "Bu günkü vade tarihine düşen sözleşmelerin anlık durumu."

  Kullanım: run_krs_pipeline(company_id, date(2026,6,22), mod='daily')
  → ~33 sözleşme (örnek dosyayla örtüşür)

AYLIK MOD (mod='monthly') — Ay sonu tam bildirim:
  Tüm aktif sözleşmelerin KRS durumu güncellenir.
  BDDK'ya gönderilecek ay sonu raporu için bu mod kullanılır.

  Kullanım: run_krs_pipeline(company_id, date(2026,6,30), mod='monthly')
  → Tüm aktif sözleşmeler (~portföy büyüklüğü kadar)

Bu fonksiyon idempotent'tir: aynı (company, rapor_tarihi) için tekrar
çalıştırıldığında önceki sonuçları silip yeniden üretir.
"""

from __future__ import annotations

import logging
from datetime import date
from itertools import groupby
from operator import itemgetter
from typing import Literal, Optional
from datetime import datetime, date

from django.db import transaction

from .. import models
from .kapama import (
    KapamaSatiri,
    classify_risk_group,
    fifo_kapama,
    hesapla_acik_durum,
    normalize_fatura_odeme,
)
from .mssql import fetch_kapama_hareketleri

from leasing.models import Lease
from contracts.models import Contract
from krs.models import *

logger = logging.getLogger(__name__)

Mod = Literal["daily", "monthly"]


def _row_tarih(row: dict) -> date:
    t = row["Tarih"]
    return t.date() if hasattr(t, "date") else t


def _row_to_satir(row: dict) -> KapamaSatiri:
    fatura, odeme = normalize_fatura_odeme(row["fatura_tutar"], row["odeme_tutar"])
    return KapamaSatiri(
        contract_header_id=int(row["ContractHeaderId"]),
        tarih=_row_tarih(row),
        fatura_tutar=fatura,
        odeme_tutar=odeme,
        odenmis_temerrut=row.get("odenen_temerrut") or 0,
        gercek_odeme_tutar=row.get("odeme_kaydi") or 0,
        protokol=row.get("protokol") or 0,
    )


@transaction.atomic
def run_krs_pipeline(
    company_id: int,
    rapor_tarihi: Optional[date] = None,
    mod: Mod = "daily",
) -> int:
    """
    Belirtilen şirket için KRS pipeline'ını çalıştırır.

    Parameters
    ----------
    company_id   : Company PK
    rapor_tarihi : Rapor tarihi; verilmezse bugün.
    mod          : 'daily'   → sadece o günkü vadeler (IFS günlük mod)
                   'monthly' → tüm aktif sözleşmeler (ay sonu tam bildirim)

    Returns
    -------
    KrsTemerrutHavuz'a yazılan sözleşme sayısı.
    """
    rapor_tarihi = rapor_tarihi or date.today()

    # ── 1. Leasflex'ten tüm hareket geçmişini çek ─────────────────────────────
    # FIFO'nun doğru çalışması için sözleşmenin tüm fatura/ödeme geçmişi gerekli.
    # Bu yüzden tarih filtresi SORGUYA değil, aşağıdaki adım 2'ye uygulanır.
    rows = list(fetch_kapama_hareketleri())
    if not rows:
        logger.warning("KRS pipeline: Leasflex'ten hiç satır gelmedi (company=%s)", company_id)
        return 0

    # ── 2. Günlük mod: yalnızca rapor_tarihi'nde vadesi gelen sözleşmeler ─────
    if mod == "daily":
        # IFS mantığı: o günkü TrnDueDate'i olan sözleşmelerin tamamı seçilir.
        # Seçilen sözleşmelerin TÜM geçmiş satırları FIFO için tutulur.
        aktif_cids: set[int] = {
            int(r["ContractHeaderId"])
            for r in rows
            if _row_tarih(r) == rapor_tarihi
        }
        if not aktif_cids:
            logger.warning(
                "KRS pipeline (daily): %s tarihi için vadeli sözleşme bulunamadı. "
                "Leasflex'teki TrnDueDate değerlerini kontrol edin.",
                rapor_tarihi,
            )
        logger.info(
            "KRS pipeline (daily, %s): %s sözleşme seçildi (toplam %s'den)",
            rapor_tarihi, len(aktif_cids), len(set(int(r["ContractHeaderId"]) for r in rows)),
        )
    else:
        # Aylık mod: tüm sözleşmeler
        aktif_cids = {int(r["ContractHeaderId"]) for r in rows}
        logger.info(
            "KRS pipeline (monthly, %s): %s sözleşmenin tamamı işleniyor",
            rapor_tarihi, len(aktif_cids),
        )

    # ── 3. FIFO eşleştirme ve temerrüt hesabı ─────────────────────────────────
    kapama_objs: list[KapamaHareketi] = []
    detay_objs:  list[KapamaDetay]    = []
    havuz_objs:  list[KrsTemerrutHavuz] = []
    report_objs: list[KrsReport] = []

    for contract_id, group in groupby(rows, key=itemgetter("ContractHeaderId")):
        cid = int(contract_id)
        if cid not in aktif_cids:
            continue  # Bu modda kapsama girmiyor

        satirlar = [_row_to_satir(r) for r in group]
        detaylar = fifo_kapama(satirlar, rapor_tarihi)
        durum = hesapla_acik_durum(satirlar, rapor_tarihi)
        risk_grubu = classify_risk_group(durum["en_eski_acik_fatura_gecikme_gun"])

        for s in satirlar:
            kapama_objs.append(KapamaHareketi(
                company_id=company_id,
                contract_header_id=s.contract_header_id,
                tarih=s.tarih,
                fatura_tutar=s.fatura_tutar,
                odeme_tutar=s.odeme_tutar,
                kapatilan_fatura_tutar=s.kapatilan_fatura_tutar,
                temerrut_tutar=s.temerrut_tutar,
                bugune_kadar_temerrut=s.bugune_kadar_temerrut,
                odenmis_temerrut=s.odenmis_temerrut,
                gercek_odeme_tutar=s.gercek_odeme_tutar,
                protokol=s.protokol,
                sentetik=s.sentetik,
            ))
        for d in detaylar:
            detay_objs.append(KapamaDetay(
                company_id=company_id,
                contract_header_id=d.contract_header_id,
                odeme_tarihi=d.odeme_tarihi,
                fatura_tarihi=d.fatura_tarihi,
                kapatilan_tutar=d.kapatilan_tutar,
            ))
        havuz_objs.append(KrsTemerrutHavuz(
            company_id=company_id,
            contract_header_id=cid,
            rapor_tarihi=rapor_tarihi,
            en_eski_acik_fatura_tarihi=durum["en_eski_acik_fatura_tarihi"],
            en_eski_acik_fatura_gecikme_gun=durum["en_eski_acik_fatura_gecikme_gun"],
            toplam_acik_bakiye=durum["toplam_acik_bakiye"],
            toplam_bugune_kadar_temerrut=durum["toplam_bugune_kadar_temerrut"],
            risk_grubu=risk_grubu,
        ))

        contract = Contract.objects.filter(contract_id=str(contract_id)).first()
        if contract:
            if contract.currency.code == "TRY":
                doviz_kodu = "949"
            elif contract.currency.code == "USD":
                doviz_kodu = "840"
            elif contract.currency.code == "EUR":
                doviz_kodu = "978"
            else:
                doviz_kodu = "000"

        lease = Lease.objects.filter(contract=contract, is_last_project=True,is_last_project_arinet=True, lease_status__in=["aktiflestirildi"]).first() if contract else None

        report_objs.append(KrsReport(
            company_id=company_id,
            contract=contract,
            lease=lease,
            kayit_turu=KayitTuru.CS0100,
            versiyon=Versiyon._01,
            uye_kodu="00309",
            portfoy_kodu="309",
            portfoy_alt_kodu="00",
            hesap_numarasi=str(contract_id).ljust(20),
            sube_kodu="  ",
            birim_kodu="  ",
            hesapla_iliskili_kisi_sayisi="1",
            doviz_kodu=doviz_kodu,
            doviz_boleni="0",
            ozel_talimat_gostergesi="  ",
            acilis_tarihi=lease.activation_date.strftime("%Y%m%d") if lease and lease.activation_date else "00000000",
            basvuru_referans_numarasi="                    ",
            kredi_turu=KrediTuru._03,
            faiz_orani_gostergesi=FaizOraniGostergesi._1,
            kredi_kullanim_amaci=KrediKullanimAmaci._12
        ))

    # ── 4. Postgres'e yaz ──────────────────────────────────────────────────────
    KapamaHareketi.objects.filter(company_id=company_id).delete()
    KapamaDetay.objects.filter(company_id=company_id).delete()
    KrsTemerrutHavuz.objects.filter(
        company_id=company_id, rapor_tarihi=rapor_tarihi
    ).delete()
    KrsReport.objects.filter(company_id=company_id).delete()

    KapamaHareketi.objects.bulk_create(kapama_objs, batch_size=1000)
    KapamaDetay.objects.bulk_create(detay_objs, batch_size=1000)
    KrsTemerrutHavuz.objects.bulk_create(havuz_objs, batch_size=1000)
    KrsReport.objects.bulk_create(report_objs, batch_size=1000)

    logger.info(
        "KRS pipeline tamamlandı (company=%s, %s, mod=%s): %s sözleşme, %s kapama, %s detay, %s rapor",
        company_id, rapor_tarihi, mod,
        len(havuz_objs), len(kapama_objs), len(detay_objs), len(report_objs),
    )
    return len(havuz_objs)
