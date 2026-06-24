"""
Kullanım:
    python manage.py export_krs_report 2
    python manage.py export_krs_report 2 --rapor-tarihi 2026-06-22
    python manage.py export_krs_report 2 --cikti /tmp/KrsBildirimi_20260622.txt

Bağımlılıklar (çalışmadan önce hazır olması gereken):
    1. run_krs_pipeline çalışmış ve KrsTemerrutHavuz dolu olmalı
    2. Lease.contract FK alanı Contract'a bağlı olmalı
    3. Contract.contract_id = IFS ContractHeaderId (sayısal string)
    4. Contract.partner FK, Partner modeline bağlı olmalı

Alan eşlemeleri (IFS ekranından doğrulandı):
    CS0100 → Contract.contract_id     = Sözleşme No
    [58:66] → Lease.activation_date   = Açılış Tarihi
    [103:113] → Lease.total_payment   = Toplam sözleşme tutarı (kuruş)
    [113:123] → KrsTemerrutHavuz.toplam_bugune_kadar_temerrut = Gecikme faizi
    [127:137] → Lease.installment_amount = Aylık taksit (tutar_C)
    [184:185] → KrsTemerrutHavuz.risk_grubu  = Risk grubu
    [186:196] → (total_payment - paid) = Kalan anapara
    [205:216] → KrsTemerrutHavuz.toplam_acik_bakiye = Gecikmedeki anapara
    TC kimlik → '16' + Partner.tc_no  (IFS: kimlik_tipi=6, 11 hane TC)

Versiyon No (01/02) mantığı:
    Eğer bu rapor tarihi için KrsTemerrutHavuz'da kontratın daha önceki
    bir kaydı yoksa → CS010002 (yeni, müşteri+adres dahil edilir).
    Önceki bir kayıt varsa → CS010001 (mevcut, sadece finansal güncelleme).
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from krs.services.report_generator import (
    ContractKrsData,
    generate_report,
)
from krs import models as krs_models


def _parse_date(s):
    if not s:
        return date.today()
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise CommandError(f"Geçersiz tarih formatı: {exc}")


def _risk_int(risk_grubu_str: str | None) -> int:
    mapping = {"grup_1": 1, "grup_2": 2, "grup_3": 3, "grup_4": 4, "grup_5": 5}
    return mapping.get(risk_grubu_str or "", 0)


def _format_adres(partner) -> str:
    parts = []
    if getattr(partner, "address", ""):
        parts.append(partner.address.strip())
    if getattr(partner, "city", None):
        parts.append(str(partner.city).strip())
    if getattr(partner, "district", None):
        parts.append(str(partner.district).strip())
    return "  ".join(p for p in parts if p)


class Command(BaseCommand):
    help = "KRS bildirim dosyasını üretir (IFS / BDDK formatı, UTF-8 BOM)."

    def add_arguments(self, parser):
        parser.add_argument("company_id", type=int)
        parser.add_argument("--rapor-tarihi", type=str, default=None)
        parser.add_argument("--cikti", type=str, default=None)

    def handle(self, *args, **options):
        company_id = options["company_id"]
        rapor_tarihi = _parse_date(options["rapor_tarihi"])

        # ── Company bilgisi ────────────────────────────────────────────────────
        # TODO: import yolunu projenize göre düzeltin
        from common.models import Company
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            raise CommandError(f"Company {company_id} bulunamadı.")
        company_name = getattr(company, "name", str(company))

        # ── 1. KrsTemerrutHavuz → bu rapor tarihi için kayıtlar ───────────────
        havuz_qs = (
            krs_models.KrsTemerrutHavuz.objects
            .filter(company_id=company_id, rapor_tarihi=rapor_tarihi)
            .order_by("contract_header_id")
        )
        if not havuz_qs.exists():
            raise CommandError(
                f"Company {company_id} için {rapor_tarihi} tarihli KRS verisi yok.\n"
                f"`python manage.py run_krs_pipeline {company_id}` önce çalıştırın."
            )

        # ── 2. Daha önce raporlanan sözleşmeler → CS010001 vs CS010002 ─────────
        previously_reported = set(
            krs_models.KrsTemerrutHavuz.objects
            .filter(company_id=company_id, rapor_tarihi__lt=rapor_tarihi)
            .values_list("contract_header_id", flat=True)
        )

        # ── 3. Contract ve Lease tablolarını yükle ─────────────────────────────
        #
        # Contract.contract_id = IFS'teki ContractHeaderId (sayısal string, ör. "49860")
        # KrsTemerrutHavuz.contract_header_id = aynı değerin integer hali (49860)
        #
        # TODO: Lease modelinin bulunduğu app'e göre import düzeltin.
        from leasing.models import Lease  # veya doğru import yolu
        from contracts.models import Contract  # veya doğru import yolu
        from partners.models import Partner  # veya doğru import yolu

        havuz_by_cid = {h.contract_header_id: h for h in havuz_qs}
        cid_strings = [str(cid) for cid in havuz_by_cid]

        # Contract: contract_id CharField ile eşleşiyoruz
        contracts_by_cid = {
            int(c.contract_id): c
            for c in Contract.objects.filter(
                company_id=company_id,
                contract_id__in=cid_strings,
            ).select_related("partner", "partner__city", "currency")
            if c.contract_id and c.contract_id.isdigit()
        }

        # Lease: her sözleşme için en uygun aktif lease'i seçiyoruz.
        # Birden fazla lease varsa activation_date'e göre en yeni aktif olanı alır.
        leases_qs = (
            Lease.objects.filter(
                company_id=company_id,
                contract__contract_id__in=cid_strings,
            )
            .select_related("contract", "currency")
            .order_by("contract__contract_id", "-activation_date")
        )
        leases_by_cid: dict[int, Lease] = {}
        for lease in leases_qs:
            try:
                cid = int(lease.contract.contract_id)
            except (ValueError, AttributeError):
                continue
            if cid not in leases_by_cid:  # ilk = en yeni (ORDER BY -activation_date)
                leases_by_cid[cid] = lease

        # ── 4. ContractKrsData listesi oluştur ────────────────────────────────
        contracts: list[ContractKrsData] = []

        for cid, h in havuz_by_cid.items():
            contract = contracts_by_cid.get(cid)
            lease = leases_by_cid.get(cid)
            partner: Partner | None = contract.partner if contract else None

            # Tarih: IFS Açılış Tarihi = Lease.activation_date
            ref_date = (
                (lease.activation_date or lease.signature_date)
                if lease
                else rapor_tarihi
            )
            if ref_date is None:
                ref_date = rapor_tarihi

            # Finansal alanlar
            total_payment = (lease.total_payment if lease else Decimal("0")) or Decimal("0")
            paid = (lease.paid if lease else Decimal("0")) or Decimal("0")
            kalan_anapara = max(total_payment - paid, Decimal("0"))
            aylik_taksit = (lease.installment_amount if lease else Decimal("0")) or Decimal("0")
            gecikme_faizi = h.toplam_bugune_kadar_temerrut or Decimal("0")

            # CS010001 mi CS010002 mi?
            is_new = cid not in previously_reported

            # Partner (müşteri) bilgileri
            tc_no = (getattr(partner, "tc_no", "") or "") if partner else ""
            soyadi = (getattr(partner, "last_name", "") or "") if partner else ""
            adi = (getattr(partner, "first_name", "") or "") if partner else ""
            baba_adi = (getattr(partner, "father_name", "") or "") if partner else ""
            anne_adi = (getattr(partner, "anne_adi", "") or "") if partner else ""  # alanda varsa
            dogum = (getattr(partner, "birthday", None)) if partner else None
            adres = _format_adres(partner) if partner else ""

            contracts.append(ContractKrsData(
                contract_header_id=cid,
                reference_date=ref_date,
                is_new=is_new,
                risk_grubu=_risk_int(h.risk_grubu),
                toplam_acik_bakiye=h.toplam_acik_bakiye or Decimal("0"),
                total_payment=total_payment,
                kalan_anapara=kalan_anapara,
                gecikme_faizi=gecikme_faizi,
                aylik_taksit=aylik_taksit,
                teminat_kodu="104",  # TODO: Lease/Contract'taki teminat alanından türet
                tc_no=tc_no,
                soyadi=soyadi,
                adi=adi,
                anne_adi=anne_adi,
                baba_adi=baba_adi,
                dogum_tarihi=dogum,
                adres=adres,
            ))

        # ── 5. Rapor üret ─────────────────────────────────────────────────────
        report_bytes = generate_report(
            contracts=contracts,
            company_name=company_name,
            period_start=rapor_tarihi,
            period_end=rapor_tarihi,
        )

        # ── 6. Dosyaya yaz ────────────────────────────────────────────────────
        out_path = options["cikti"] or os.path.join(
            settings.BASE_DIR,
            "files",
            "krs",
            f"KrsBildirimi_{rapor_tarihi.strftime('%y%m%d')}.txt",
        )
        with open(out_path, "wb") as f:
            f.write(report_bytes)

        self.stdout.write(self.style.SUCCESS(
            f"{len(contracts)} sözleşme → {out_path} ({len(report_bytes):,} bayt)"
        ))
