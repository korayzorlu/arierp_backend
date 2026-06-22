"""
krs/services/pipeline.py

Tüm KRS akışını baştan sona koşan orkestrasyon katmanı:
  1. Leasflex (MSSQL) -> kapama hareketlerini çek
  2. Sözleşme bazında grupla
  3. İşaret normalizasyonu + FIFO eşleştirme + temerrüt hesapları
  4. Açık durum özetini çıkar, risk grubunu belirle
  5. Sonuçları Postgres'e yaz (KapamaHareketi, KapamaDetay, KrsTemerrutHavuz)

Bu fonksiyon idempotent'tir: aynı (company, rapor_tarihi) için tekrar
çalıştırıldığında önceki sonuçları silip yeniden üretir - orijinal
PL/SQL'deki "DELETE + yeniden INSERT" davranışıyla aynı.
"""

from __future__ import annotations

import logging
from datetime import date
from itertools import groupby
from operator import itemgetter
from typing import Optional

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

logger = logging.getLogger(__name__)


def _row_to_satir(row: dict) -> KapamaSatiri:
    fatura, odeme = normalize_fatura_odeme(row["fatura_tutar"], row["odeme_tutar"])
    tarih = row["Tarih"]
    tarih = tarih.date() if hasattr(tarih, "date") else tarih
    return KapamaSatiri(
        contract_header_id=int(row["ContractHeaderId"]),
        tarih=tarih,
        fatura_tutar=fatura,
        odeme_tutar=odeme,
        odenmis_temerrut=row.get("odenen_temerrut") or 0,
        gercek_odeme_tutar=row.get("odeme_kaydi") or 0,
        protokol=row.get("protokol") or 0,
    )


@transaction.atomic
def run_krs_pipeline(company_id: int, rapor_tarihi: Optional[date] = None) -> int:
    """
    Belirtilen şirket için KRS pipeline'ını çalıştırır.

    Dönüş: rapor üretilen sözleşme sayısı.
    """
    rapor_tarihi = rapor_tarihi or date.today()

    rows = list(fetch_kapama_hareketleri())
    if not rows:
        logger.warning("KRS pipeline: Leasflex'ten hiç satır gelmedi (company=%s)", company_id)

    kapama_objs: list[models.KapamaHareketi] = []
    detay_objs: list[models.KapamaDetay] = []
    havuz_objs: list[models.KrsTemerrutHavuz] = []

    for contract_id, group in groupby(rows, key=itemgetter("ContractHeaderId")):
        satirlar = [_row_to_satir(r) for r in group]
        detaylar = fifo_kapama(satirlar, rapor_tarihi)
        durum = hesapla_acik_durum(satirlar, rapor_tarihi)
        risk_grubu = classify_risk_group(durum["en_eski_acik_fatura_gecikme_gun"])

        for s in satirlar:
            kapama_objs.append(
                models.KapamaHareketi(
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
                )
            )
        for d in detaylar:
            detay_objs.append(
                models.KapamaDetay(
                    company_id=company_id,
                    contract_header_id=d.contract_header_id,
                    odeme_tarihi=d.odeme_tarihi,
                    fatura_tarihi=d.fatura_tarihi,
                    kapatilan_tutar=d.kapatilan_tutar,
                )
            )
        havuz_objs.append(
            models.KrsTemerrutHavuz(
                company_id=company_id,
                contract_header_id=contract_id,
                rapor_tarihi=rapor_tarihi,
                en_eski_acik_fatura_tarihi=durum["en_eski_acik_fatura_tarihi"],
                en_eski_acik_fatura_gecikme_gun=durum["en_eski_acik_fatura_gecikme_gun"],
                toplam_acik_bakiye=durum["toplam_acik_bakiye"],
                toplam_bugune_kadar_temerrut=durum["toplam_bugune_kadar_temerrut"],
                risk_grubu=risk_grubu,
            )
        )

    # Bu şirket için kapama tablolarını sıfırdan yeniden kuruyoruz (orijinal
    # "DELETE FROM TRLEAS_KAPAMA_TAB" + yeniden INSERT davranışıyla aynı).
    models.KapamaHareketi.objects.filter(company_id=company_id).delete()
    models.KapamaDetay.objects.filter(company_id=company_id).delete()
    # KrsTemerrutHavuz tarihsel bir snapshot tablosu olduğu için SADECE bu
    # rapor_tarihi'ne ait önceki kayıtlar silinir, geçmiş tarihler korunur
    # (orijinal Temerrut_Havuzu'nun "DELETE WHERE rapor_tarihi=tarih2_"
    # davranışıyla aynı).
    models.KrsTemerrutHavuz.objects.filter(company_id=company_id, rapor_tarihi=rapor_tarihi).delete()

    models.KapamaHareketi.objects.bulk_create(kapama_objs, batch_size=1000)
    models.KapamaDetay.objects.bulk_create(detay_objs, batch_size=1000)
    models.KrsTemerrutHavuz.objects.bulk_create(havuz_objs, batch_size=1000)

    logger.info(
        "KRS pipeline tamamlandı (company=%s, rapor_tarihi=%s): %s sözleşme, %s kapama satırı, %s detay",
        company_id, rapor_tarihi, len(havuz_objs), len(kapama_objs), len(detay_objs),
    )
    return len(havuz_objs)
